import hashlib
import random

class ChameleonHash:
    def __init__(self):
        # 使用 RFC 3526 标准的 1536-bit MODP Group 安全素数
        # 保证 q 是素数，且 p = 2q + 1 也是素数，彻底避免数学求逆出错
        p_hex = (
            "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
            "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
            "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
            "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
            "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE65381"
            "FFFFFFFFFFFFFFFF"
        )
        self.p = int(p_hex, 16)
        self.q = (self.p - 1) // 2
        self.g = 2  # 阶为 q 的生成元

    def _hash_message(self, message: str) -> int:
        """将任意字符串消息映射为一个整数 m"""
        h = hashlib.sha256(message.encode()).hexdigest()
        # 取哈希值转为整数，并限制在 q 的范围内
        return int(h, 16) % self.q

    def keygen(self):
        """对应论文中的 KGen: 生成净化者的陷门私钥 x 和哈希公钥 y"""
        x = random.randint(1, self.q - 1)  # 陷门私钥 td
        y = pow(self.g, x, self.p)         # 哈希公钥 hk
        return x, y

    def hash(self, y, message, r):
        """
        对应论文中的 Hash: 计算变色龙哈希值
        h = (g^m * y^r) mod p
        """
        m = self._hash_message(message)
        term1 = pow(self.g, m, self.p)
        term2 = pow(y, r, self.p)
        h = (term1 * term2) % self.p
        return h

    def adapt(self, x, message, r, new_message):
        """
        对应论文中的 Adapt: 净化者利用陷门私钥 x，为新消息计算出能产生相同哈希值的新随机数 r'
        r' = (m - m') * x^(-1) + r mod q
        """
        m = self._hash_message(message)
        m_prime = self._hash_message(new_message)
        
        # 使用 Python 3.8+ 内置的方法求模反元素，代替不稳定的手写算法
        x_inv = pow(x, -1, self.q)
        
        r_prime = ((m - m_prime) * x_inv + r) % self.q
        return r_prime

# ================= 测试代码 =================
if __name__ == "__main__":
    ch = ChameleonHash()
    
    # 1. 净化者生成密钥
    trapdoor_key, hash_key = ch.keygen()
    print("--- 初始化阶段 ---")
    print(f"陷门私钥 (仅净化者可见): {trapdoor_key}")
    print(f"哈希公钥 (全网公开): {hash_key}\n")

    # 2. 原始交易
    msg_original = "Patient: Alice, Disease: Heart Disease, Amount: 100"
    r_original = random.randint(1, ch.q - 1)
    
    hash_original = ch.hash(hash_key, msg_original, r_original)
    print("--- 原始数据上链 ---")
    print(f"原始消息: '{msg_original}'")
    print(f"原始随机数: {r_original}")
    print(f"原始哈希值: {hash_original}\n")

    # 3. 净化交易（脱敏隐藏姓名）
    msg_sanitized = "Patient: ***, Disease: Heart Disease, Amount: 100"
    
    # 净化者使用陷门计算新随机数
    r_new = ch.adapt(trapdoor_key, msg_original, r_original, msg_sanitized)
    
    hash_new = ch.hash(hash_key, msg_sanitized, r_new)
    print("--- 净化脱敏处理 ---")
    print(f"净化后消息: '{msg_sanitized}'")
    print(f"计算出的新随机数: {r_new}")
    print(f"净化后哈希值: {hash_new}\n")

    # 4. 验证是否碰撞成功
    if hash_original == hash_new:
        print("🎉 成功！变色龙哈希碰撞验证通过，内容已修改但哈希值完全一致！")
    else:
        print("❌ 失败！哈希值不一致。")