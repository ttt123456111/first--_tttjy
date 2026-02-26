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

# ================= 业务流测试 =================
if __name__ == "__main__":
    # 1. 初始化区块链与 SMS 密码系统
    bc = Blockchain()
    trapdoor, hk, endorsers = bc.sms.setup_system(num_endorsers=3)
    endorser_vks = [kp[1] for kp in endorsers]
    endorser_sks = [kp[0] for kp in endorsers]
    
    print("======== 1. 卖家发起数据交易 ========")
    original_data = "卖家: 张三, 数据集: 10万条带姓名体检报告, 定价: 500 Token"
    
    # 背书节点对原始数据签名
    r_val, agg_sig = bc.sms.sign(original_data, hk, endorser_sks)
    tx1 = Transaction("TX_1001", original_data, r_val, hk, agg_sig, endorser_vks)
    print(f"已生成带多重签名的交易。当前内容: '{tx1.payload}'\n")
    
    print("======== 2. 监管介入：合规脱敏 (Sanitization) ========")
    # 监管机构要求隐藏真实姓名才能上链交易
    sanitized_data = "卖家: ***, 数据集: 10万条[已脱敏]体检报告, 定价: 500 Token"
    
    # 执行净化，并留下“操作者指纹”以供追责
    tx1.sanitize(bc.sms, trapdoor, sanitized_data, operator_id="Data_Regulator_007")
    print(f"数据已合规脱敏: '{tx1.payload}'")
    print(f"🕵️ 追责审计日志已生成: {tx1.sanitization_log}\n")
    
    print("======== 3. 交易广播与区块链打包 ========")
    # 模拟将这笔被修改过的交易广播到区块链网络
    is_accepted = bc.add_new_transaction(tx1)
    
    if is_accepted:
        print("✅ 矿工验证：SMS 签名验证通过！即使数据被改过，原始多方背书依然有效。")
        new_block = bc.mine()
        print(f"📦 交易已成功打包至区块高度: {new_block.index}")
        print(f"🔗 区块哈希: {new_block.hash}")
    else:
        print("❌ 交易验证失败，被网络拒绝。")