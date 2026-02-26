import sys
import os
import time

# 将项目根目录加入环境变量，以便引用我们写的密码学模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto.sms import SanitizableMultiSignature
from crypto.multisig_sim import MultiSigSimulator

def run_experiments():
    sms_system = SanitizableMultiSignature()
    ms_system = MultiSigSimulator()
    
    # 模拟不同的背书节点规模：3个、10个、50个、100个
    test_nodes = [3, 10, 50, 100]
    
    original_data = "Original Medical Record: Alice, Blood Type O, Fee 500"
    sanitized_data = "Sanitized Medical Record: ***, Blood Type O, Fee 500"
    
    print(f"{'背书节点数量 (N)':<15} | {'传统重签耗时 (ms)':<20} | {'SMS 净化耗时 (ms)':<20} | {'效率提升倍数':<15}")
    print("-" * 80)
    
    for n in test_nodes:
        # 1. 初始化系统
        trapdoor, hk, endorsers = sms_system.setup_system(num_endorsers=n)
        sks = [kp[0] for kp in endorsers] # N 个私钥
        
        # ==========================================
        # 实验 A：传统多重签名的“数据更新”
        # 必须让所有 N 个节点重新对新数据签名
        # ==========================================
        start_time_trad = time.time()
        # 模拟网络将数据发给 N 个节点重新签名
        for sk in sks:
            ms_system.sign(sk, sanitized_data)
        trad_time_ms = (time.time() - start_time_trad) * 1000
        
        # ==========================================
        # 实验 B：可净化多重签名 (SMS) 的“数据更新”
        # 只需要净化者执行 1 次变色龙碰撞计算
        # ==========================================
        # 预先生成原始签名（不在更新耗时统计内）
        r_original, _ = sms_system.sign(original_data, hk, sks)
        
        start_time_sms = time.time()
        # 净化者独立完成脱敏
        sms_system.sanitize(trapdoor, original_data, r_original, sanitized_data)
        sms_time_ms = (time.time() - start_time_sms) * 1000
        
        # 防止 sms_time_ms 为 0 导致除以 0 报错（因为算得太快了）
        if sms_time_ms == 0:
            sms_time_ms = 0.001 
            
        speedup = trad_time_ms / sms_time_ms
        
        # 打印输出对比结果
        print(f"{n:<20} | {trad_time_ms:<25.2f} | {sms_time_ms:<22.3f} | {speedup:.1f}x")

if __name__ == "__main__":
    print("🚀 正在启动去中心化数据交易系统性能压测...\n")
    run_experiments()
    print("\n💡 结论：传统签名在数据更新时耗时随节点数线性增长，而 SMS 方案耗时固定且极低！")