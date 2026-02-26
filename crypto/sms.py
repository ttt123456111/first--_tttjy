import sys
import os
# 确保能够正确导入同级目录下的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import random
from chameleon import ChameleonHash
from multisig_sim import MultiSigSimulator

class SanitizableMultiSignature:
    def __init__(self):
        self.ch = ChameleonHash()
        self.ms = MultiSigSimulator()

    def setup_system(self, num_endorsers=3):
        """初始化整个系统的密钥"""
        # 1. 净化者生成变色龙哈希密钥对
        trapdoor_key, hash_key = self.ch.keygen()
        
        # 2. 生成若干个背书节点的 ECDSA 密钥对
        endorsers = [self.ms.keygen() for _ in range(num_endorsers)]
        return trapdoor_key, hash_key, endorsers

    def sign(self, message: str, hash_key: int, endorser_priv_keys: list):
        """
        背书节点进行签名：
        【核心修复】：只对变色龙哈希值 h 进行签名！
        """
        # 1. 选取初始随机数 r
        r = random.randint(1, self.ch.q - 1)
        
        # 2. 计算变色龙哈希 h
        h = self.ch.hash(hash_key, message, r)
        
        # 3. 构造签名载荷 Payload（只放 h，因为 h 在净化前后绝对不会变！）
        payload = str(h)
        
        # 4. 背书节点进行多重签名聚合
        individual_sigs = [self.ms.sign(sk, payload) for sk in endorser_priv_keys]
        agg_sig = self.ms.aggregate_signatures(individual_sigs)
        
        return r, agg_sig

    def sanitize(self, trapdoor_key: int, original_msg: str, original_r: int, new_msg: str):
        """
        净化者修改消息：
        计算出一个新的随机数 r'，使得新消息的哈希值与原来一致。
        """
        r_new = self.ch.adapt(trapdoor_key, original_msg, original_r, new_msg)
        return r_new

    def verify(self, message: str, r: int, hash_key: int, agg_sig: str, endorser_pub_keys: list):
        """
        验证者验证签名：
        计算当前消息的哈希，并验证多重签名是否对该哈希有效。
        """
        # 1. 计算当前(可能被净化过)消息的变色龙哈希 h
        h = self.ch.hash(hash_key, message, r)
        
        # 2. 重构载荷（同样只验证 h）
        payload = str(h)
        
        # 3. 验证多签
        return self.ms.verify_aggregate(endorser_pub_keys, payload, agg_sig)

# ================= 业务流程模拟 =================
if __name__ == "__main__":
    sms = SanitizableMultiSignature()
    
    print("======== 1. 系统初始化 ========")
    trapdoor, hk, endorsers = sms.setup_system(num_endorsers=3)
    endorser_vks = [kp[1] for kp in endorsers]
    endorser_sks = [kp[0] for kp in endorsers]
    print("净化者陷门与哈希公钥已生成。")
    print(f"成功注册 {len(endorsers)} 个背书节点。\n")

    print("======== 2. 原始交易与背书 ========")
    original_tx = "Patient: Tang Jingyun, Disease: Mild Fever, Fee: 50"
    print(f"原始数据: '{original_tx}'")
    
    r_val, aggregated_signature = sms.sign(original_tx, hk, endorser_sks)
    print(f"背书完毕。生成的初始随机数 r: {r_val}")
    print("由于是对哈希值签名，原始签名已牢牢绑定在变色龙哈希上。\n")

    print("======== 3. 净化者脱敏处理 (Sanitization) ========")
    sanitized_tx = "Patient: ***, Disease: Mild Fever, Fee: 50"
    print(f"净化后数据: '{sanitized_tx}'")
    
    new_r_val = sms.sanitize(trapdoor, original_tx, r_val, sanitized_tx)
    print(f"净化者悄悄计算出的新随机数 r': {new_r_val}")
    print("注意：多重签名 aggregated_signature 没有任何改动！\n")

    print("======== 4. 最终验证环节 ========")
    is_valid = sms.verify(sanitized_tx, new_r_val, hk, aggregated_signature, endorser_vks)
    if is_valid:
        print("✅ 验证成功！\n原理：验证者拿到新数据和新随机数，算出的哈希依然是最初背书节点看到的那个哈希。这就是可净化多签名的魔力！")
    else:
        print("❌ 验证失败！")