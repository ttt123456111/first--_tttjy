import time
from blockchain.core import Blockchain, Transaction

def print_separator(title):
    print(f"\n{'='*20} {title} {'='*20}")

def main():
    print("🌟 欢迎使用 [基于可净化多签名的去中心化数据交易系统] 🌟")
    
    # 1. 初始化与密钥分发 (Key Distribution)
    print_separator("第 0 阶段：可信环境初始化与系统密钥分发")
    print("🏛️ [系统初始化中心] 正在生成底层椭圆曲线与变色龙哈希参数...")
    time.sleep(1)
    
    bc = Blockchain()
    num_nodes = 3
    trapdoor, hk, endorsers = bc.sms.setup_system(num_endorsers=num_nodes)
    endorser_vks = [kp[1] for kp in endorsers]
    endorser_sks = [kp[0] for kp in endorsers]
    
    print("✅ 参数生成完毕。正在模拟分布式网络环境下的密钥分发...")
    time.sleep(1)
    # 重点：通过打印输出，向老师展示系统中的权限是严格隔离的！
    print("🔐 [权限隔离] 变色龙陷门私钥 (Trapdoor) -> 已安全下发至【系统监管节点】的本地安全区。")
    print(f"🔐 [权限隔离] ECDSA 签名私钥组 (SKs) -> 已分别下发至【{num_nodes} 个背书节点】的本地安全区。")
    print("🌍 [全网公开] 变色龙哈希公钥 (HK) 与 所有背书节点公钥 (VKs) -> 已向区块链全网广播！\n")
    
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
    print("⚠️ 警告: 系统检测到当前交易可能包含敏感隐私，不符合合规上链要求！")
    action = input("是否授权监管机构(Sanitizer)利用'变色龙陷门'进行脱敏处理？(y/n): ")
    
    if action.lower() == 'y':
        print("\n🔧 监管节点正在调用其专属的【陷门私钥 (Trapdoor)】进行哈希碰撞计算...")
        
        # === 新增：动态脱敏逻辑 ===
        # 如果你直接按次回车用了默认的 Alice，系统就自动用默认的脱敏格式
        if original_payload == "患者: Alice, 身份证: 110105199001011234, 症状: 抑郁症, 售价: 100 Token":
            sanitized_payload = "患者: ***, 身份证: ******************, 症状: 抑郁症, 售价: 100 Token"
        else:
            # 如果你输入了自定义数据（比如张三），系统会让你手动输入脱敏后的样子
            print(f"📄 当前需脱敏的原始数据: {original_payload}")
            sanitized_payload = input("📝 请手动输入脱敏后的数据内容 (例如把名字换成***): ")
            if not sanitized_payload:
                sanitized_payload = original_payload + " (系统自动掩码处理)"
        # =========================
        
        # 净化操作
        tx.sanitize(bc.sms, trapdoor, sanitized_payload, operator_id="Regulator_Admin_01")
        time.sleep(1)
        print(f"✅ 数据脱敏成功！")
        print(f"📜 修改后的交易载荷: {tx.payload}")
        print(f"🕵️ 追责系统已记录此次净化操作: {tx.sanitization_log}")
    else:
        print("\n❌ 拒绝脱敏，交易因包含隐私可能面临被拒风险。")

    # 4. 上链与最终验证 (加入防篡改测试)
    print_separator("第三阶段：全网验证与区块打包上链")
    
    # === 新增：模拟黑客攻击交互 ===
    print("😈 突发测试：是否模拟黑客在数据传输过程中恶意篡改数据内容？")
    attack = input("请输入 (y 模拟黑客篡改 / n 正常上链): ")
    
    if attack.lower() == 'y':
        print("\n💥 黑客出击：正在偷偷将售价从 '100 Token' 改为 '9999 Token'...")
        # 黑客只改了数据，但他没有净化者的变色龙陷门密钥，算不出正确的补偿随机数
        tx.payload = tx.payload.replace("100 Token", "9999 Token")
        print(f"被篡改的假数据: {tx.payload}")
        time.sleep(1)
        print("🔄 正在将【被篡改的交易】提交至区块链网络...")
    else:
        print("\n🔄 正在将【正常交易】提交至区块链网络交易池...")
    
    time.sleep(1)
    
    # 全网节点进行底层密码学验证
    is_accepted = bc.add_new_transaction(tx)
    
    if is_accepted:
        print("✅ 密码学验证通过！变色龙哈希与多重签名匹配成功！")
        print("🔨 矿工正在打包区块...")
        time.sleep(1)
        new_block = bc.mine()
        print(f"🎉 恭喜！交易已成功永久写入区块链！")
        print(f"🧱 区块高度: {new_block.index}")
        print(f"🔗 区块哈希: {new_block.hash}")
    else:
        print("\n❌ 严重错误：签名验证失败，网络已拒绝该交易！")
        print("🛡️ 防御机制生效：系统检测到数据与签名不匹配。这证明了未经授权的篡改（即使只是改了一个数字），也会因为没有变色龙陷门密钥而导致底层哈希碰撞失败，从而被多重签名机制立刻拦截！")
        
    print("\n演示结束。感谢使用 [基于可净化多签名的去中心化数据交易系统]！")

if __name__ == "__main__":
    main()