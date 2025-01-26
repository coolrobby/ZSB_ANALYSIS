import pandas as pd
import streamlit as st
import altair as alt
import os

# 设置页面标题
st.title("作业统计")

# 读取当前目录下的作业统计.xlsx文件
selected_file = '作业统计.xlsx'

# 检查文件是否存在
if os.path.exists(selected_file):
    # 读取数据
    df = pd.read_excel(selected_file)

    # 清理列名，去除可能的空格
    df.columns = df.columns.str.strip()

    # 处理缺失值：将空字符串替换为 NaN
    df.replace('', pd.NA, inplace=True)

    # 获取所有可用的作业
    available_dates = df['作业'].unique()
    
    # 用户选择的作业
    selected_dates = st.multiselect("选择查看的作业", available_dates, default=available_dates)

    # 获取所有可用的课程
    available_courses = df['课程'].unique()
    
    # 用户选择的课程
    selected_courses = st.multiselect("选择查看的课程", available_courses, default=available_courses)

    if selected_dates:
        # 过滤选择的作业数据
        df_filtered = df[df['作业'].isin(selected_dates)]

        # 如果用户选择了课程，则过滤课程
        if selected_courses:
            df_filtered = df_filtered[df_filtered['课程'].isin(selected_courses)]

        # 获取所有可用的维度（列名），如果没有选择课程，就去除“课程”维度
        available_dimensions = [
            '学校', '院系', '专业', '行政班级', '授课班级', '教师'
        ]
        
        if selected_courses:
            available_dimensions.append('课程')  # 如果选择了课程，则显示“课程”维度

        # 用户选择的维度
        selected_dimension = st.selectbox("选择分析的维度", available_dimensions, index=1)  # 默认选择“院系”

        if selected_dimension:
            # 动态分组，按用户选择的维度进行分组
            groupby_columns = [selected_dimension]

            # 按选定维度进行合并统计：计算成绩的平均值、及格人数和及格率
            avg_watch_time_by_dimension = df_filtered.groupby(groupby_columns).agg(
                总人次=('姓名', 'size'),
                平均成绩=('成绩', 'mean'),  # 计算平均成绩
                及格人数=('成绩', lambda x: (x >= 60).sum())  # 计算及格人数，假设60分及格
            ).reset_index()

            # 计算及格率
            avg_watch_time_by_dimension['及格率'] = (avg_watch_time_by_dimension['及格人数'] / avg_watch_time_by_dimension['总人次']) * 100

            # 确保成绩是数值格式，并且去除无效值
            avg_watch_time_by_dimension['平均成绩'] = pd.to_numeric(avg_watch_time_by_dimension['平均成绩'], errors='coerce')
            avg_watch_time_by_dimension['及格率'] = pd.to_numeric(avg_watch_time_by_dimension['及格率'], errors='coerce')

            # 处理NaN和无效值，将它们设为0或者其他默认值
            avg_watch_time_by_dimension['平均成绩'] = avg_watch_time_by_dimension['平均成绩'].fillna(0)
            avg_watch_time_by_dimension['及格率'] = avg_watch_time_by_dimension['及格率'].fillna(0)

            # 用户选择排序依据：按“及格率”或“平均成绩”
            sort_by = st.radio("选择排序依据", ('及格率', '平均成绩'), index=0)  # 默认按“及格率”排序
            ascending = st.radio("选择排序方式", ('降序', '升序'), index=0)  # 默认降序

            # 对数据按选择的列进行排序
            avg_watch_time_by_dimension_sorted = avg_watch_time_by_dimension.sort_values(by=sort_by, ascending=(ascending == '升序'))

            # 创建柱形图并排序
            st.subheader(f"按 {selected_dimension} 维度分析")

            # 创建柱形图，X轴为选定的排序列，Y轴为选择的维度
            bar_chart = alt.Chart(avg_watch_time_by_dimension_sorted).mark_bar().encode(
                x=alt.X(sort_by, sort='-x' if ascending == '降序' else 'x'),  # 根据选择的排序列
                y=alt.Y(selected_dimension, sort='-x' if ascending == '降序' else 'x'),  # Y轴为维度列，按选定排序列排序
                tooltip=[selected_dimension, '总人次', '平均成绩', '及格率']
            ).properties(
                title=f"{selected_dimension} 的成绩及及格率分析"
            )

            st.altair_chart(bar_chart, use_container_width=True)

            # 构建每个维度的信息表格
            table_data = []

            for index, row in avg_watch_time_by_dimension_sorted.iterrows():
                # 将每个维度的信息添加到表格数据
                table_row = {selected_dimension: row[selected_dimension]}
                table_row.update({
                    "总人次": row['总人次'],
                    "平均成绩": f"{row['平均成绩']:.2f}",  # 显示平均成绩，带两位小数
                    "及格率": f"{row['及格率']:.2f}%"  # 显示及格率，带两位小数并加上百分号
                })
                table_data.append(table_row)

            # 显示表格，按照用户选择的列排序
            df_table = pd.DataFrame(table_data)
            df_table[sort_by] = pd.to_numeric(df_table[sort_by], errors='coerce')
            st.table(df_table.sort_values(by=sort_by, ascending=(ascending == '升序')))

else:
    st.error("当前目录下没有找到'作业统计.xlsx'文件。")
