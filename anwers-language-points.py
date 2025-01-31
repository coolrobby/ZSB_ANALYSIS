import pandas as pd
import streamlit as st
import altair as alt
import os

# 设置页面标题
st.title("知识点掌握度分析")

# 读取当前目录下的答题情况分析.xlsx文件
selected_file = '答题情况分析.xlsx'

# 检查文件是否存在
if os.path.exists(selected_file):
    # 读取数据
    df = pd.read_excel(selected_file)

    # 清理列名，去除可能的空格
    df.columns = df.columns.str.strip()

    # 处理缺失值：将空字符串替换为 NaN
    df.replace('', pd.NA, inplace=True)

    # 将签到状态“已签”和“教师代签”视为出勤，其他为缺勤
    df['答题情况'] = df['核对答案'].apply(lambda x: '正确' if x in ['正确'] else '错误')

    # 获取所有可用的知识点
    available_dates = df['知识点'].unique()

    # 获取所有可用的课程
    available_courses = df['课程'].unique()

    # 获取所有可用的来源
    available_sources = df['来源'].unique() if '来源' in df.columns else []

    # 用户选择的知识点、课程和来源
    selected_dates = st.multiselect("选择查看的知识点", available_dates, default=available_dates)
    selected_courses = st.multiselect("选择查看的课程", available_courses, default=available_courses)
    selected_sources = st.multiselect("选择查看的作业/测试", available_sources, default=available_sources)

    # 选项：是否显示“答错学生”
    show_absent_students = st.checkbox("显示答错学生", value=False)

    if selected_dates:
        # 过滤选择的知识点数据
        df_filtered = df[df['知识点'].isin(selected_dates)]

        # 如果用户选择了课程，则过滤课程
        if selected_courses:
            df_filtered = df_filtered[df_filtered['课程'].isin(selected_courses)]

        # 如果用户选择了来源，则过滤来源
        if selected_sources:
            df_filtered = df_filtered[df_filtered['来源'].isin(selected_sources)]

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
                答对人次=('答题情况', lambda x: (x == '正确').sum()),
                答错人次=('答题情况', lambda x: (x == '错误').sum())
            ).reset_index()

            # 计算正确率，去掉百分号，只显示数字
            attendance_by_dimension['正确率'] = (attendance_by_dimension['答对人次'] / attendance_by_dimension['总人次']) * 100

            # 确保正确率是数值格式，并且去除无效值
            attendance_by_dimension['正确率'] = pd.to_numeric(attendance_by_dimension['正确率'], errors='coerce')

            # 处理NaN和无效值，将它们设为0或者其他默认值
            attendance_by_dimension['正确率'] = attendance_by_dimension['正确率'].fillna(0)

            # 对数据按正确率降序或升序排列
            sort_order = st.radio("选择排序方式", ('降序', '升序'), index=0)  # 默认降序
            ascending = False if sort_order == '降序' else True

            # 对数据按正确率排序
            attendance_by_dimension_sorted = attendance_by_dimension.sort_values(by='正确率', ascending=ascending)

            # 创建柱形图并排序
            st.subheader(f"按 {selected_dimension} 维度分析")

            # 创建柱形图，X轴为正确率，Y轴为选择的维度
            bar_chart = alt.Chart(attendance_by_dimension_sorted).mark_bar().encode(
                x=alt.X('正确率', sort='-x' if not ascending else 'x'),  # 确保根据升降序选择排序
                y=alt.Y(selected_dimension, sort='-x' if not ascending else 'x'),  # Y轴为维度列，按正确率排序
                tooltip=[selected_dimension, '总人次', '答对人次', '答错人次', '正确率']
            ).properties(
                title=f"{selected_dimension} 的答题情况"
            )

            st.altair_chart(bar_chart, use_container_width=True)

            # 构建每个维度的信息表格
            table_data = []

            for index, row in attendance_by_dimension_sorted.iterrows():
                # 查找答错学生
                absent_names_str = ""
                if show_absent_students:
                    absent_students = df_filtered[ 
                        (df_filtered[selected_dimension] == row[selected_dimension]) & 
                        (df_filtered['答题情况'] == '错误')
                    ]

                    absent_names = absent_students['姓名'].tolist()
                    absent_names_set = set(absent_names)  # 去重
                    absent_names_str = ", ".join(sorted(absent_names_set)) if absent_names_set else "所有学生都已经答对"

                # 将每个维度的信息添加到表格数据
                table_row = {selected_dimension: row[selected_dimension]}
                table_row.update({
                    "总人次": row['总人次'],
                    "答对人次": row['答对人次'],
                    "正确率": f"{row['正确率']:.2f}",  # 显示正确率为数字，带两位小数
                    "答错人次": row['答错人次'],
                    "答错学生": absent_names_str if show_absent_students else ""
                })
                table_data.append(table_row)

            # 显示表格，按照正确率排序
            # 强制将“正确率”列的值转为数值类型，以确保正确排序
            df_table = pd.DataFrame(table_data)
            df_table['正确率'] = pd.to_numeric(df_table['正确率'], errors='coerce')
            st.table(df_table.sort_values(by='正确率', ascending=ascending))

else:
    st.error("当前目录下没有找到'答题情况分析.xlsx'文件。")
