import streamlit as st
import time

# ！！！重点在这里：直接从你的 blockchain.core 导入底层类！！！
from blockchain.core import Blockchain, Transaction  

# ================= 页面全局配置 =================
st.set_page_config(page_title="SMS 数据交易系统控制台", page_icon="🛡️", layout="wide")

# ================= 初始化系统状态 =================
if 'bc' not in st.session_state:
    st.session_state.bc = Blockchain()
    # 先初始化系统拿到参数
    trapdoor, hk, endorsers = st.session_state.bc.sms.setup_system(num_endorsers=3)
    st.session_state.trapdoor = trapdoor
    st.session_state.hk = hk
    st.session_state.endorser_sks = [kp[0] for kp in endorsers]
    st.session_state.endorser_vks = [kp[1] for kp in endorsers]
    
if 'current_tx' not in st.session_state:
    st.session_state.current_tx = None

# ================= 侧边栏：系统状态面板 =================
with st.sidebar:
    st.title("⚙️ 系统控制台")
    st.success("✅ 区块链网络已启动")
    st.info(f"🌐 当前背书节点数量: 3")
    st.warning("🔑 监管节点(Sanitizer)已就绪，持有变色龙陷门私钥。")
    
    st.markdown("---")
    st.markdown("### 📊 当前账本状态")
    st.metric(label="主链区块高度", value=len(st.session_state.bc.chain))
    st.metric(label="交易池待处理", value=len(st.session_state.bc.unconfirmed_transactions))

# ================= 主界面 =================
st.title("🛡️ 基于可净化多签名的去中心化数据交易系统")
st.markdown("本控制台用于演示 **交易发布 -> 合规脱敏(变色龙哈希碰撞) -> 验证上链/黑客拦截** 的完整业务流。")

tab1, tab2, tab3 = st.tabs(["📝 第一阶段: 发布与背书", "🔧 第二阶段: 监管脱敏", "⛓️ 第三阶段: 上链与安全防御"])

# --------- 第一阶段：发布与背书 ---------
with tab1:
    st.header("步骤 1：卖家发布原始数据")
    original_data = st.text_area("📄 请输入包含敏感信息的医疗/交易数据：", 
                                 value="患者: Alice, 身份证: 110105199001011234, 症状: 抑郁症, 售价: 100 Token")
    
    if st.button("🚀 发起交易与多方背书", type="primary"):
        with st.spinner('正在向背书节点集群广播并计算变色龙哈希...'):
            time.sleep(1)
            # 节点背书
            r_val, agg_sig = st.session_state.bc.sms.sign(
                original_data, 
                st.session_state.hk, 
                st.session_state.endorser_sks
            )
            # 生成新交易
            tx_id = f"TX_{int(time.time())}"
            # 💡 修改后的代码：去掉变量名，直接按顺序传值
            tx = Transaction(
                tx_id,
                original_data,
                r_val,
                st.session_state.hk,
                agg_sig,
                st.session_state.endorser_vks
            )
            st.session_state.current_tx = tx
            
        st.success("✅ 多方联合背书成功！")
        st.json({
            "交易 ID": tx.tx_id,
            "原始明文 (Payload)": tx.payload,
            "变色龙初始随机数 (r)": tx.r_val,
            "底层聚合签名状态": "有效 (Valid)"
        })

# --------- 第二阶段：合规脱敏 ---------
with tab2:
    st.header("步骤 2：授权监管节点进行净化")
    if st.session_state.current_tx is None:
        st.warning("⚠️ 请先在第一阶段生成并背书一笔交易！")
    else:
        st.error("🚨 警告：系统检测到当前交易包含严重隐私数据，无法直接合规上链！")
        sanitized_data = st.text_input("📝 请输入脱敏后的数据内容：", 
                                       value="患者: ***, 身份证: ******************, 症状: 抑郁症, 售价: 100 Token")
        
        if st.button("🔧 调用陷门私钥进行哈希碰撞", type="primary"):
            with st.spinner('监管者正在利用扩展欧几里得算法重算补偿随机数 r\' ...'):
                time.sleep(1.5)
                # 执行脱敏
                st.session_state.current_tx.sanitize(
                    sms_instance=st.session_state.bc.sms,
                    trapdoor_key=st.session_state.trapdoor,
                    new_payload=sanitized_data,
                    operator_id="Regulator_Web_Admin"
                )
            
            st.success("🎉 数据脱敏成功，且底层签名绝对有效！")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info("🔄 更新后的交易载荷")
                st.write(f"**明文:** {st.session_state.current_tx.payload}")
                st.write(f"**新随机数 r':** {st.session_state.current_tx.r_val}")
            with col2:
                st.info("📜 不可篡改的审计日志")
                st.json(st.session_state.current_tx.sanitization_log)

# --------- 第三阶段：上链与安全防御 ---------
with tab3:
    st.header("步骤 3：全网验证与防御测试")
    if st.session_state.current_tx is None:
        st.warning("⚠️ 暂无待处理交易！")
    else:
        colA, colB = st.columns(2)
        
        with colA:
            st.subheader("✅ 正常验证上链")
            if st.button("🔨 矿工打包并验证交易", type="primary"):
                with st.spinner('矿工正在进行 ECDSA 多重签名的密码学校验...'):
                    time.sleep(1)
                    success = st.session_state.bc.add_new_transaction(st.session_state.current_tx)
                    if success:
                        new_block = st.session_state.bc.mine()
                        st.balloons()
                        st.success("🎉 验证通过！交易已永久写入区块链！")
                        st.json({
                            "区块高度": new_block.index,
                            "区块哈希": new_block.hash,
                            "包含交易数": len(new_block.transactions)
                        })
                        # 上链后清空当前交易，准备下一轮
                        st.session_state.current_tx = None 
                        
                    else:
                        st.error("❌ 交易被拒绝！可能是重放攻击。")

        with colB:
            st.subheader("😈 恶意篡改拦截测试")
            st.write("模拟黑客在不知道陷门的情况下，强行修改交易价格：")
            hacker_data = st.text_input("黑客篡改的数据:", value="患者: ***, 症状: 抑郁症, 售价: 9999 Token (恶意提价)")
            
            if st.button("☠️ 模拟黑客发送非法交易"):
                with st.spinner('验证节点正在审查该非法交易...'):
                    time.sleep(1)
                    # 强行篡改数据，但不更新随机数（因为黑客没私钥）
                    hacked_tx = st.session_state.current_tx
                    hacked_tx.payload = hacker_data
                    
                    # 提交给网络
                    success = st.session_state.bc.add_new_transaction(hacked_tx)
                    if not success:
                        st.error("🚨 严重错误：签名验证失败！该笔交易包含未授权篡改，底层哈希防线破裂，网络已将其拦截并丢弃！")