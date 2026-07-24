# learning_analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def generate_analysis(user_data):
    """
    根据用户真实数据生成学情看板
    """
    if not user_data:
        st.info("暂无用户数据，快去对话学习吧！")
        return

    tasks = user_data.get("待办任务", [])
    
    if not tasks:
        st.info("目前还没有任务记录。添加或完成一些任务后，这里将自动生成分析图表。")
        return

    st.subheader("📊 我的学习数据看板")
    st.caption("基于你真实的任务完成情况动态生成")

    # 1. 数据清洗与核心指标计算
    completed_tasks = [t for t in tasks if t.get("状态") == "已完成"]
    pending_tasks = [t for t in tasks if t.get("状态") != "已完成"]
    
    total = len(tasks)
    completed = len(completed_tasks)
    completion_rate = round((completed / total) * 100, 1) if total > 0 else 0

    # 2. 指标卡片展示
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 总任务量", total)
    col2.metric("✅ 已完成", completed, delta=f"{completion_rate}% 完成率")
    
    # 计算正在进行的任务数量
    in_progress = len([t for t in tasks if t.get("状态") == "未完成"])
    col3.metric("⏳ 未完成", in_progress)

    st.divider()

    # 3. 时间趋势分析图表 (真实展示任务完成进度)
    # 提取日期字段（如果任务没有日期，会落到"未归类"中）
    task_df = pd.DataFrame(tasks)
    
    # 如果有截止时间，尝试解析为标准日期格式（用于绘图）
    if "截止时间" in task_df.columns:
        # 简单处理：把符合日期格式的截止时间变成纯日期列
        # 注意：此处依赖 parse_deadline_to_date 的逻辑，为了独立运行，这里做个简单的提取
        task_df['绘图日期'] = task_df['截止时间'].apply(lambda x: '近期' if any(k in str(x) for k in ['今天','明天','后天','周']) else '长期规划')
    
    # 统计不同状态的分布
    status_counts = task_df['状态'].value_counts().reset_index()
    status_counts.columns = ['状态', '数量']
    
    # 4. 任务状态分布饼图
    fig_pie = px.pie(
        status_counts, 
        values='数量', 
        names='状态', 
        title="📌 任务状态分布全景",
        color_discrete_map={'已完成': '#00CC96', '未完成': '#EF553B'},
        hole=0.4  # 甜甜圈样式，更好看
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # 5. 结合日期的柱状图 (体现动态趋势)
    # 将状态映射为 1 (完成) 和 0 (未完成) 用于图表展示逻辑
    if "截止时间" in task_df.columns:
        # 筛选出有明确时间属性的任务做趋势分析
        task_with_date = task_df[task_df['绘图日期'] != '长期规划']
        if not task_with_date.empty:
            trend_counts = task_with_date.groupby(['绘图日期', '状态']).size().reset_index(name='数量')
            
            fig_bar = px.bar(
                trend_counts,
                x='绘图日期',
                y='数量',
                color='状态',
                title="📈 近期任务时间分布趋势",
                barmode='group',
                color_discrete_map={'已完成': '#00CC96', '未完成': '#EF553B'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.caption("暂未检测到具体日期的近期任务，趋势图等待数据更新。")

    # 6. 拓展建议（展示AI的智能洞察）
    if completion_rate > 80:
        st.success("💪 任务完成率极高，保持这个节奏，你是最棒的！")
    elif completion_rate > 50:
        st.info("💡 进度不错，注意优先完成紧急且重要的任务。")
    else:
        st.warning("⏰ 任务积压较多，建议先完成最紧急的 2-3 项，或者让我帮您拆分复杂任务。")