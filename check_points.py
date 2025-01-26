import pandas as pd
import streamlit as st
import altair as alt
import os

# 设置页面标题
st.title("任务点完成详情13")

# 读取当前目录下的任务点完成详情.xlsx文件
selected_file = '任务点完成详情.xlsx'

# 检查文件是否存在
if os.path.exists(selected_file):
    # 读取数据
    df = pd.read_excel(selected_file)

    # 清理列名，去除可能的空格
    df.columns = df.columns.str.strip()

    # 处理缺失值：将空字符串替换为 NaN
    df.replace('', pd.NA, inplace=True)

    # 将签到状态“已签”和“教师代签”视为出勤，其他为缺勤
    df['完成情况'] = df['详情'].apply(lambda x: '已完成' if x in ['已完成'] else '未完成')

    # 获取所有可用的任务点
    available_dates = df['任务点'].unique()
    
    # 用户选择的任务点
    selected_dates = st.multiselect("选择查看的任务点", available_dates, default=available_dates)

    # 获取所有可用的课程
    available_courses = df['课程'].unique()
    
    # 用户选择的课程
    selected_courses = st.multiselect("选择查看的课程", available_courses, default=available_courses)
    
    # 选项：是否显示“未完成学生”
    show_absent_students = st.checkbox("显示未完成学生", value=False)

    if selected_dates:
        # 过滤选择的任务点数据
        df_filtered = df[df['任务点'].isin(selected_dates)]

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

            # 按选定维度进行合并统计：计算总人次、出勤人次和缺勤人次
            attendance_by_dimension = df_filtered.groupby(groupby_columns).agg(
                总人次=('姓名', 'size'),
                已完成人次=('完成情况', lambda x: (x == '已完成').sum()),
                未完成人次=('完成情况', lambda x: (x == '未完成').sum())
            ).reset_index()

            # 计算完成率，去掉百分号，只显示数字
            attendance_by_dimension['完成率'] = (attendance_by_dimension['已完成人次'] / attendance_by_dimension['总人次']) * 100

            # 确保完成率是数值格式，并且去除无效值
            attendance_by_dimension['完成率'] = pd.to_numeric(attendance_by_dimension['完成率'], errors='coerce')

            # 处理NaN和无效值，将它们设为0或者其他默认值
            attendance_by_dimension['完成率'] = attendance_by_dimension['完成率'].fillna(0)

            # 对数据按完成率降序或升序排列
            sort_order = st.radio("选择排序方式", ('降序', '升序'), index=0)  # 默认降序
            ascending = False if sort_order == '降序' else True

            # 对数据按完成率排序
            attendance_by_dimension_sorted = attendance_by_dimension.sort_values(by='完成率', ascending=ascending)

            # 创建柱形图并排序
            st.subheader(f"按 {selected_dimension} 维度分析")

            # 创建柱形图，X轴为完成率，Y轴为选择的维度
            bar_chart = alt.Chart(attendance_by_dimension_sorted).mark_bar().encode(
                x=alt.X('完成率', sort='-x' if not ascending else 'x'),  # 确保根据升降序选择排序
                y=alt.Y(selected_dimension, sort='-x' if not ascending else 'x'),  # Y轴为维度列，按完成率排序
                tooltip=[selected_dimension, '总人次', '已完成人次', '未完成人次', '完成率']
            ).properties(
                title=f"{selected_dimension} 的任务完成情况"
            )

            st.altair_chart(bar_chart, use_container_width=True)

            # 构建每个维度的信息表格
            table_data = []

            for index, row in attendance_by_dimension_sorted.iterrows():
                # 查找未完成学生
                absent_names_str = ""
                if show_absent_students:
                    absent_students = df_filtered[ 
                        (df_filtered[selected_dimension] == row[selected_dimension]) & 
                        (df_filtered['完成情况'] == '未完成')
                    ]

                    absent_names = absent_students['姓名'].tolist()
                    absent_names_str = ", ".join(absent_names) if absent_names else "所有学生都已经完成任务"

                # 将每个维度的信息添加到表格数据
                table_row = {selected_dimension: row[selected_dimension]}
                table_row.update({
                    "总人次": row['总人次'],
                    "已完成人次": row['已完成人次'],
                    "完成率": f"{row['完成率']:.2f}",  # 显示完成率为数字，带两位小数
                    "未完成人次": row['未完成人次'],
                    "未完成学生": absent_names_str if show_absent_students else ""
                })
                table_data.append(table_row)

            # 显示表格，按照柱形图排序顺序显示
            st.table(pd.DataFrame(table_data).set_index(selected_dimension).sort_values(by='完成率', ascending=ascending))

else:
    st.error("当前目录下没有找到'任务点完成详情.xlsx'文件。")
