import pandas as pd
import streamlit as st
import os

# 设置页面标题
st.title("任务点完成详情")

# 自动读取当前目录下所有的xlsx文件
file_list = [f for f in os.listdir() if f.endswith('.xlsx')]

if file_list:
    # 确保文件名为出勤.xlsx
    selected_file = '任务点完成详情.xlsx' 
    
    # 读取数据
    df = pd.read_excel(selected_file)

    # 清理列名，去除可能的空格
    df.columns = df.columns.str.strip()

    # 处理缺失值：将空字符串替换为 NaN
    df.replace('', pd.NA, inplace=True)

    # 用默认日期填充空值（2000年1月1日），可以防止 NaT 错误
    df['时间'] = df['时间'].fillna(pd.to_datetime('2000-01-01'))

    # 将签到状态“已签”和“教师代签”视为出勤，其他为缺勤
    df['出勤状态'] = df['签到状态'].apply(lambda x: '出勤' if x in ['已签', '教师代签'] else '缺勤')

    # 只考虑不是2000-01-01的时间
    df_filtered = df[df['时间'] != pd.to_datetime('2000-01-01')]

    # 获取所有可用的时间（日期）
    available_dates = df_filtered['时间'].unique()
    
    # 用户选择的日期
    selected_dates = st.multiselect("选择查看的日期", available_dates, default=available_dates)

    # 获取所有可用的课程
    available_courses = df_filtered['课程'].unique()
    
    # 用户选择的课程
    selected_courses = st.multiselect("选择查看的课程", available_courses, default=available_courses)

    if selected_dates:
        # 过滤选择的日期数据并合并数据
        df_filtered = df_filtered[df_filtered['时间'].isin(selected_dates)]

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

            # 按选定维度进行合并统计：计算总人数、出勤人数和缺勤人数
            attendance_by_dimension = df_filtered.groupby(groupby_columns).agg(
                总人数=('姓名', 'size'),
                出勤人数=('出勤状态', lambda x: (x == '出勤').sum()),
                缺勤人数=('出勤状态', lambda x: (x == '缺勤').sum())
            ).reset_index()

            # 计算出勤率
            attendance_by_dimension['出勤率'] = (attendance_by_dimension['出勤人数'] / attendance_by_dimension['总人数']) * 100

            # 创建一个新的列，确保出勤率为 100% 的数据排在前面
            attendance_by_dimension['排序出勤率'] = attendance_by_dimension['出勤率'].apply(lambda x: -1 if x == 100 else x)

            # 对数据按出勤率降序排列
            attendance_by_dimension_sorted = attendance_by_dimension.sort_values(by=['排序出勤率', '出勤率'], ascending=[True, False])

            # 显示合并后的柱形图，按照出勤率降序排序
            st.subheader(f"按 {selected_dimension} 维度分析")
            st.bar_chart(attendance_by_dimension_sorted.set_index(selected_dimension)['出勤率'])

            # 构建每个维度的信息表格
            table_data = []

            for index, row in attendance_by_dimension_sorted.iterrows():
                # 查找缺勤学生
                absent_students = df_filtered[
                    (df_filtered[selected_dimension] == row[selected_dimension]) & 
                    (df_filtered['出勤状态'] == '缺勤')
                ]

                absent_names = absent_students['姓名'].tolist()
                absent_names_str = ", ".join(absent_names) if absent_names else "没有缺勤学生"

                # 将每个维度的信息添加到表格数据
                table_row = {selected_dimension: row[selected_dimension]}
                table_row.update({
                    "总人数": row['总人数'],
                    "出勤人数": row['出勤人数'],
                    "出勤率": f"{row['出勤率']:.2f}%",
                    "缺勤人数": row['缺勤人数'],
                    "缺勤学生": absent_names_str
                })
                table_data.append(table_row)

            # 显示表格，按出勤率降序排列
            st.table(pd.DataFrame(table_data).sort_values(by='出勤率', ascending=False))
else:
    st.error("当前目录下没有找到任何xlsx文件。")
