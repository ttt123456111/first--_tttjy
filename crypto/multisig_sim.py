import hashlib
import json
import base64
from ecdsa import SigningKey, SECP256k1
from ecdsa.keys import BadSignatureError  # 👉 修复了这里的导入路径

class MultiSigSimulator:
    def __init__(self):
        # 使用业界标准的 SECP256k1 椭圆曲线（比特币和众多区块链的基础曲线）
        self.curve = SECP256k1

    def keygen(self):
        """生成参与者的 ECDSA 密钥对 (私钥, 公钥)"""
        sk = SigningKey.generate(curve=self.curve)
        vk = sk.verifying_key
        return sk, vk

    def sign(self, sk, message: str) -> str:
        """单人对消息进行签名，返回 Base64 格式的签名字符串"""
        # 使用 SHA-256 对消息进行哈希处理后再签名
        sig_bytes = sk.sign(message.encode('utf-8'), hashfunc=hashlib.sha256)
        return base64.b64encode(sig_bytes).decode('utf-8')

    def aggregate_signatures(self, signatures: list) -> str:
        """
        模拟签名聚合 (Signature Aggregation)。
        在真正的 Schnorr/MuSig2 中，这里是复杂的曲线点运算。
        在我们的原型系统中，我们将多个签名序列化打包成一个紧凑的 JSON 字符串，
        以此模拟多方背书合并为一个“聚合签名”的过程。
        """
        return json.dumps(signatures)

    def verify_aggregate(self, vks: list, message: str, agg_sig_str: str) -> bool:
        """
        验证聚合签名。
        系统只需调用一次此函数，即可完成对所有背书人的验证。
        """
        try:
            signatures = json.loads(agg_sig_str)
            # 签名数量必须和公钥数量一致
            if len(vks) != len(signatures):
                print("❌ 验证失败：签名数量与公钥数量不匹配！")
                return False

            # 遍历验证每一个参与者的签名
            for vk, sig_b64 in zip(vks, signatures):
                sig_bytes = base64.b64decode(sig_b64)
                # 如果内部任何一个签名伪造或消息被篡改，这里会抛出异常
                vk.verify(sig_bytes, message.encode('utf-8'), hashfunc=hashlib.sha256)
            
            return True
        except BadSignatureError:
            print("❌ 验证失败：发现无效或被篡改的签名！")
            return False
        except Exception as e:
            print(f"❌ 验证出错：{e}")
            return False

# ================= 测试代码 =================
if __name__ == "__main__":
    ms_sim = MultiSigSimulator()
    
    print("--- 1. 初始化背书节点 (Endorsers) ---")
    # 模拟 3 个背书节点（比如数据交易系统中的 3 个监管机构）
    endorsers = [ms_sim.keygen() for _ in range(3)]
    private_keys = [kp[0] for kp in endorsers]
    public_keys = [kp[1] for kp in endorsers]
    print(f"成功生成 {len(endorsers)} 个背书节点的密钥对。\n")

    print("--- 2. 生成多方背书签名 ---")
    tx_proposal = "Data_ID: 9527, Action: Trade, Price: 500 ETH"
    print(f"待背书的交易提案: '{tx_proposal}'")
    
    # 每个节点独立签名
    individual_sigs = [ms_sim.sign(sk, tx_proposal) for sk in private_keys]
    
    # 将多个签名聚合为一个
    aggregated_signature = ms_sim.aggregate_signatures(individual_sigs)
    print(f"\n生成的模拟聚合签名 (前50个字符...): {aggregated_signature[:50]}...")
    print(f"签名总大小: {len(aggregated_signature)} 字节\n")

    print("--- 3. 验证聚合签名 ---")
    # 正常验证流程
    is_valid = ms_sim.verify_aggregate(public_keys, tx_proposal, aggregated_signature)
    if is_valid:
        print("🎉 成功！所有背书节点的签名均验证通过。")
        
    print("\n--- 4. 模拟黑客篡改数据 ---")
    tampered_proposal = "Data_ID: 9527, Action: Trade, Price: 9999 ETH"  # 黑客偷偷改了价格
    print(f"被篡改的提案: '{tampered_proposal}'")
    
    # 期待验证失败
    print("正在验证被篡改的数据...")
    is_valid_tampered = ms_sim.verify_aggregate(public_keys, tampered_proposal, aggregated_signature)
    if not is_valid_tampered:
        print("🛡️ 拦截成功！系统检测出数据被篡改，普通签名防御生效。")