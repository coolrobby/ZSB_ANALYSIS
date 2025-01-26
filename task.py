import pandas as pd
import streamlit as st
import altair as alt
import os

# 设置页面标题
st.title("作业统计2")

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

    # 如果成绩为空，视为缺考
    df['成绩'] = df['成绩'].fillna('缺考')

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

            # 按选定维度进行合并统计：计算成绩的平均值、及格人数、缺考人数等
            stats_by_dimension = df_filtered.groupby(groupby_columns).agg(
                总人次=('姓名', 'size'),
                平均成绩=('成绩', lambda x: pd.to_numeric(x[x != '缺考'], errors='coerce').mean()),  # 计算平均成绩，排除缺考
                及格人数=('成绩', lambda x: (pd.to_numeric(x[x != '缺考'], errors='coerce') >= 60).sum()),  # 计算及格人数，排除缺考
                实考人次=('成绩', lambda x: (x != '缺考').sum()),  # 计算有成绩的人数
                缺考人数=('成绩', lambda x: (x == '缺考').sum()),  # 计算缺考人数
                缺考名单=('姓名', lambda x: ", ".join(x[df['成绩'] == '缺考'])),  # 计算缺考名单
                最高分=('成绩', lambda x: pd.to_numeric(x[x != '缺考'], errors='coerce').max()),  # 计算最高分，排除缺考
                最低分=('成绩', lambda x: pd.to_numeric(x[x != '缺考'], errors='coerce').min())  # 计算最低分，排除缺考
            ).reset_index()

            # 处理计算结果中的NaN值
            stats_by_dimension['平均成绩'] = stats_by_dimension['平均成绩'].fillna(0)
            stats_by_dimension['及格人数'] = stats_by_dimension['及格人数'].fillna(0)
            stats_by_dimension['实考人次'] = stats_by_dimension['实考人次'].fillna(0)
            stats_by_dimension['缺考人数'] = stats_by_dimension['缺考人数'].fillna(0)
            stats_by_dimension['缺考名单'] = stats_by_dimension['缺考名单'].fillna('')
            stats_by_dimension['最高分'] = stats_by_dimension['最高分'].fillna(0)
            stats_by_dimension['最低分'] = stats_by_dimension['最低分'].fillna(0)

            # 生成分数段统计（每10分为一个段）
            df_filtered['成绩'] = pd.to_numeric(df_filtered['成绩'], errors='coerce')
            bins = range(0, 101, 10)  # 0-100分，每10分一个区间
            labels = [f"{i}-{i+9}" for i in bins[:-1]]
            df_filtered['分数段'] = pd.cut(df_filtered['成绩'], bins=bins, labels=labels, right=False)

            # 分数段统计
            score_range_stats = df_filtered.groupby(['作业', selected_dimension, '分数段']).agg(
                人数=('姓名', 'size')
            ).reset_index()

            # 显示分数段统计
            st.subheader(f"按分数段统计（每10分为一个段）")
            st.table(score_range_stats)

            # 默认按“平均成绩”排序
            ascending = st.radio("选择排序方式", ('降序', '升序'), index=0)  # 默认降序

            # 对数据按“平均成绩”进行排序
            stats_by_dimension_sorted = stats_by_dimension.sort_values(by='平均成绩', ascending=(ascending == '升序'))

            # 创建柱形图并排序
            st.subheader(f"按 {selected_dimension} 维度分析")

            # 创建柱形图，X轴为平均成绩，Y轴为选择的维度
            bar_chart = alt.Chart(stats_by_dimension_sorted).mark_bar().encode(
                x=alt.X('平均成绩', sort='-x' if ascending == '降序' else 'x'),  # 确保根据升降序选择排序
                y=alt.Y(selected_dimension, sort='-x' if ascending == '降序' else 'x'),  # Y轴为维度列，按平均成绩排序
                tooltip=[selected_dimension, '总人次', '平均成绩', '及格人数', '实考人次', '缺考人数', '最高分', '最低分']
            ).properties(
                title=f"{selected_dimension} 的成绩分析"
            )

            st.altair_chart(bar_chart, use_container_width=True)

            # 构建每个维度的信息表格
            table_data = []

            for index, row in stats_by_dimension_sorted.iterrows():
                # 将每个维度的信息添加到表格数据
                table_row = {selected_dimension: row[selected_dimension]}
                table_row.update({
                    "总人次": row['总人次'],
                    "平均成绩": f"{row['平均成绩']:.2f}",  # 显示平均成绩，带两位小数
                    "及格人数": row['及格人数'],
                    "实考人次": row['实考人次'],
                    "缺考人数": row['缺考人数'],
                    "缺考名单": row['缺考名单'],
                    "最高分": row['最高分'],
                    "最低分": row['最低分']
                })
                table_data.append(table_row)

            # 显示表格，按照平均成绩排序
            df_table = pd.DataFrame(table_data)
            df_table['平均成绩'] = pd.to_numeric(df_table['平均成绩'], errors='coerce')
            st.table(df_table.sort_values(by='平均成绩', ascending=(ascending == '升序')))

else:
    st.error("当前目录下没有找到'作业统计.xlsx'文件。")
