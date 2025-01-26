import pandas as pd
import streamlit as st
import os

# 设置页面标题
st.title("任务点完成情况分析")

# 自动读取当前目录下所有的xlsx文件
file_list = [f for f in os.listdir() if f.endswith('.xlsx')]

if file_list:
    # 确保文件名为任务点完成详情.xlsx
    selected_file = '任务点完成详情.xlsx'  # 假设文件名为任务点完成详情.xlsx
    
    # 读取数据
    df = pd.read_excel(selected_file)

    # 清理列名，去除可能的空格
    df.columns = df.columns.str.strip()

    # 处理缺失值：将空字符串替换为 NaN
    df.replace('', pd.NA, inplace=True)

    # 选择“详情”列进行分析
    if '详情' not in df.columns:
        st.error("表格中没有‘详情’列！")
    else:
        # 获取所有的列名
        available_columns = [col for col in df.columns if col != '详情']
        
        # 用户选择维度进行分析
        selected_column = st.selectbox("选择分析的维度", available_columns)

        if selected_column:
            # 获取用户选择维度的所有选项
            available_options = df[selected_column].dropna().unique()

            # 用户选择的具体选项
            selected_option = st.selectbox(f"选择{selected_column}的具体值", available_options)

            # 根据用户选择的维度和具体值进行过滤
            df_filtered = df[df[selected_column] == selected_option]

            # 计算任务总数、完成人数、未完成人数、完成率
            task_total = df_filtered['任务点'].nunique()  # 任务点的数量
            task_completed = df_filtered[df_filtered['完成情况'] == '完成']['任务点'].nunique()  # 完成任务的数量
            task_not_completed = task_total - task_completed  # 未完成任务的数量

            # 计算完成率
            if task_total > 0:
                completion_rate = (task_completed / task_total) * 100
            else:
                completion_rate = 0

            # 显示统计信息
            st.subheader(f"{selected_column} = {selected_option} 的任务分析")
            st.write(f"任务总数：{task_total}")
            st.write(f"完成人数：{task_completed}")
            st.write(f"未完成人数：{task_not_completed}")
            st.write(f"完成率：{completion_rate:.2f}%")

            # 创建一个交互式表格显示数据
            st.subheader(f"{selected_column} = {selected_option} 的任务详情")
            st.table(df_filtered[['任务点', '完成情况', '详情']])

else:
    st.error("当前目录下没有找到任何xlsx文件。")
