import time
from blockchain.core import Blockchain, Transaction

def print_separator(title):
    print(f"\n{'='*20} {title} {'='*20}")

def main():
    print("🌟 欢迎使用 [基于可净化多签名的去中心化数据交易系统] 🌟")
    print("正在初始化底层区块链结构与密码学环境...")
    
    # 1. 初始化
    bc = Blockchain()
    num_nodes = 3
    trapdoor, hk, endorsers = bc.sms.setup_system(num_endorsers=num_nodes)
    endorser_vks = [kp[1] for kp in endorsers]
    endorser_sks = [kp[0] for kp in endorsers]
    print(f"✅ 系统初始化完成！已接入 {num_nodes} 个背书节点。\n")
    
    # 2. 卖家发布数据
    print_separator("第一阶段：卖家发布原始数据与多方背书")
    print("提示: 卖家(Alice)准备将一份包含敏感信息的医疗数据集上链交易。")
    original_payload = input("📝 请输入要交易的原始数据 (直接回车使用默认数据): ")
    if not original_payload:
        original_payload = "患者: Alice, 身份证: 110105199001011234, 症状: 抑郁症, 售价: 100 Token"
    
    print(f"\n📡 正在广播给 {num_nodes} 个背书节点进行签名验证...")
    time.sleep(1)
    
    # 节点背书
    r_val, agg_sig = bc.sms.sign(original_payload, hk, endorser_sks)
    
    # 创建交易结构
    tx_id = f"TX_{int(time.time())}"
    tx = Transaction(tx_id, original_payload, r_val, hk, agg_sig, endorser_vks)
    print(f"✅ 多方背书完成！")
    print(f"🔒 交易ID: {tx.tx_id}")
    print(f"📜 当前交易载荷: {tx.payload}")
    
    # 3. 监管净化数据
    print_separator("第二阶段：监管节点介入净化 (脱敏处理)")
    print("⚠️ 警告: 系统检测到当前交易包含敏感隐私(姓名、身份证)，不符合合规上链要求！")
    action = input("是否授权监管机构(Sanitizer)利用'变色龙陷门'进行脱敏处理？(y/n): ")
    
    if action.lower() == 'y':
        print("\n🔧 净化者正在修改数据，并计算变色龙哈希碰撞以维持多签有效性...")
        sanitized_payload = "患者: ***, 身份证: ******************, 症状: 抑郁症, 售价: 100 Token"
        
        # 净化操作
        tx.sanitize(bc.sms, trapdoor, sanitized_payload, operator_id="Regulator_Admin_01")
        time.sleep(1)
        print(f"✅ 数据脱敏成功！")
        print(f"📜 修改后的交易载荷: {tx.payload}")
        print(f"🕵️ 追责系统已记录此次净化操作: {tx.sanitization_log}")
    else:
        print("\n❌ 拒绝脱敏，交易因包含隐私可能面临被拒风险。")

    # 4. 上链与最终验证
    print_separator("第三阶段：全网验证与区块打包上链")
    print("🔄 正在将交易提交至区块链网络交易池...")
    time.sleep(1)
    
    is_accepted = bc.add_new_transaction(tx)
    if is_accepted:
        print("✅ 密码学验证通过！不论数据是否被脱敏，基于变色龙哈希的底层多重签名依然100%匹配！")
        
        # 矿工打包
        print("🔨 矿工正在打包区块...")
        time.sleep(1)
        new_block = bc.mine()
        print(f"🎉 恭喜！交易已成功永久写入区块链！")
        print(f"🧱 区块高度: {new_block.index}")
        print(f"🔗 区块哈希: {new_block.hash}")
    else:
        print("❌ 严重错误：签名验证失败，网络拒绝了该交易。这通常是因为非授权人员篡改了数据！")
        
    print("\n演示结束。感谢使用！")

if __name__ == "__main__":
    main()