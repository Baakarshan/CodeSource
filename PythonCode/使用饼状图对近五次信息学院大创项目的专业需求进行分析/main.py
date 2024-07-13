import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 定义数据
labels = ['计算机科学', '软件工程', '人工智能', '信息', '通信', '管理', '经济', '人文科学', '环境']
sizes = [35, 25, 15, 10, 5, 4, 3, 2, 1]
explode = (0.08, 0.08, 0.08, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04)  # 仅对第一个切片“爆炸”

# 创建饼状图
fig, ax = plt.subplots(figsize=(16, 8), dpi=300)  # 增加图片宽度
wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                                  shadow=True, startangle=90, textprops={'fontsize': 12})

# 确保饼状图是圆形的
ax.axis('equal')

# 添加详细文字描述
descriptions = [
    "计算机科学: 占比35%，是需求量最大的专业，涉及编程、算法、数据结构等知识。",
    "软件工程: 占比25%，主要包括软件开发、测试和维护等方面的知识。",
    "人工智能: 占比15%，涉及机器学习、深度学习和数据挖掘等领域。",
    "信息: 占比10%，涵盖信息系统、信息管理等方面。",
    "通信: 占比5%，包括通信原理、网络通信等知识。",
    "管理: 占比4%，涉及项目管理、企业管理等。",
    "经济: 占比3%，主要包括经济学原理和应用。",
    "人文科学: 占比2%，涉及社会学、人类学等。",
    "环境: 占比1%，包括环境科学、生态学等。"
]

# 在图表右侧添加描述，增加行间距
fig.text(0.02, 0.5, "\n\n".join(descriptions), wrap=True, horizontalalignment='left', fontsize=10, verticalalignment='center', transform=plt.gcf().transFigure)

# 设置标题并移动到文字正上方
plt.text(-0.3, 0.98, '专业需求占比', fontsize=16, weight='bold', ha='left', va='center', transform=plt.gca().transAxes)

# 调整图表边距，以确保描述不会遮挡饼图
plt.subplots_adjust(left=0.3, right=0.95, top=0.85)

# 保存图表，设置 DPI 为 300
plt.savefig('分析结果.png', bbox_inches='tight', dpi=300)
