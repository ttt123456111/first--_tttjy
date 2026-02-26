import matplotlib.pyplot as plt
import os

def generate_plots():
    # 填入我们刚刚压测出来的真实数据
    nodes = [3, 10, 50, 100]
    trad_time = [3.10, 6.91, 36.15, 84.72]    # 传统重签耗时 (ms)
    sms_time = [0.149, 0.155, 0.162, 0.331]   # SMS 净化耗时 (ms)
    speedup = [20.8, 44.6, 223.0, 256.2]      # 效率提升倍数
    
    # 确保输出目录存在
    output_dir = os.path.join(os.path.dirname(__file__), 'figures')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # ==========================================
    # 图 1：耗时对比折线图 (Time Cost Comparison)
    # ==========================================
    plt.figure(figsize=(8, 5))
    plt.plot(nodes, trad_time, marker='o', linestyle='-', color='red', label='Traditional Multi-Sig (Re-signing)')
    plt.plot(nodes, sms_time, marker='s', linestyle='-', color='green', label='Proposed SMS (Sanitization)')
    
    plt.title('Time Cost of Data Update: Traditional vs Proposed SMS')
    plt.xlabel('Number of Endorsing Nodes (N)')
    plt.ylabel('Time Cost (ms)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    
    plot1_path = os.path.join(output_dir, 'time_comparison.png')
    plt.savefig(plot1_path, dpi=300, bbox_inches='tight')
    print(f"✅ 图 1 已生成并保存至: {plot1_path}")
    plt.close()

    # ==========================================
    # 图 2：效率提升倍数柱状图 (Speedup Ratio)
    # ==========================================
    plt.figure(figsize=(8, 5))
    bars = plt.bar([str(n) for n in nodes], speedup, color='#4C72B0', width=0.5)
    
    plt.title('Efficiency Speedup of Proposed SMS System')
    plt.xlabel('Number of Endorsing Nodes (N)')
    plt.ylabel('Speedup Ratio (x)')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    
    # 在柱子上打上具体的数字标签
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 5, f"{yval}x", ha='center', va='bottom', fontweight='bold')
        
    plot2_path = os.path.join(output_dir, 'speedup_comparison.png')
    plt.savefig(plot2_path, dpi=300, bbox_inches='tight')
    print(f"✅ 图 2 已生成并保存至: {plot2_path}")
    plt.close()

if __name__ == "__main__":
    print("正在根据实验数据生成论文图表...")
    generate_plots()
    print("🎉 所有实验图表生成完毕！可以插入毕业论文中使用了。")