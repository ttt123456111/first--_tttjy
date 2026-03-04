import sys
import os
import hashlib
import time
import json

# 添加项目根目录到环境变量，以便导入我们刚才写的 crypto 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto.sms import SanitizableMultiSignature

class Transaction:
    def __init__(self, tx_id, payload, r_val, hk, agg_sig, endorser_vks):
        self.tx_id = tx_id
        self.payload = payload           # 交易的具体内容（如医疗数据）
        self.r_val = r_val               # 变色龙哈希的随机数 r
        self.hk = hk                     # 变色龙哈希公钥
        self.agg_sig = agg_sig           # 核心：可净化多重签名 SMS
        self.endorser_vks = endorser_vks # 背书节点的公钥列表
        
        # 追责审计日志：记录每一次净化操作，满足开题报告中的“可追溯性”要求
        self.sanitization_log = []       

    def sanitize(self, sms_instance, trapdoor_key, new_payload, operator_id):
        """
        执行净化脱敏操作，并自动记录审计日志
        """
        # 1. 魔法发生：计算能维持哈希不变的新随机数 r'
        new_r = sms_instance.sanitize(trapdoor_key, self.payload, self.r_val, new_payload)
        
        # 2. 记录审计日志 (Accountability Mechanism)
        log_entry = {
            "operator_id": operator_id,
            "timestamp": time.time(),
            "action": "SANITIZATION",
            "original_payload": self.payload,
            "new_payload": new_payload
        }
        self.sanitization_log.append(log_entry)
        
        # 3. 更新交易内容与随机数，准备上链
        self.payload = new_payload
        self.r_val = new_r
        return True

    def is_valid(self, sms_instance):
        """调用 SMS 底层密码学算法，验证这笔交易是否合法"""
        return sms_instance.verify(self.payload, self.r_val, self.hk, self.agg_sig, self.endorser_vks)

class Block:
    def __init__(self, index, transactions, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        """计算区块的 SHA-256 哈希值（保证区块本身的不可篡改性）"""
        # 为了简化，我们只对区块头和交易数量做哈希（实际中会用默克尔树）
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "tx_count": len(self.transactions),
            "previous_hash": self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.unconfirmed_transactions = [] # 交易池
        self.chain = []                    # 已上链的区块
        self.sms = SanitizableMultiSignature()
        self.create_genesis_block()        # 创世区块

    def create_genesis_block(self):
        """生成区块链的第 0 个区块（创世区块）"""
        genesis_block = Block(0, [], "0" * 64)
        self.chain.append(genesis_block)

    def add_new_transaction(self, tx: Transaction):
        """接收全网广播的新交易，验证通过后放入交易池"""
        print(f"➡️ 收到新交易 {tx.tx_id}，正在执行全网验证...")
        
        # === 防御重放攻击 (Replay Attack) 逻辑 ===
        # 遍历链上所有区块里的交易，看这个 tx_id 是否已经处理过了
        for block in self.chain:
            for existing_tx in block.transactions:
                if existing_tx.tx_id == tx.tx_id:
                    print("🛡️ 防御生效：拒绝交易！检测到重放攻击 (交易ID已存在链上)！")
                    return False
        
        # 验证签名有效性
        if tx.is_valid(self.sms):
            self.unconfirmed_transactions.append(tx)
            return True
        return False

    def mine(self):
        """矿工将交易池中的交易打包成新区块，追加到链上"""
        if not self.unconfirmed_transactions:
            return False

        last_block = self.chain[-1]
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          previous_hash=last_block.hash)
        
        self.chain.append(new_block)
        # 清空交易池
        self.unconfirmed_transactions = []
        return new_block