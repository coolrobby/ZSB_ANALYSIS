import pandas as pd
import streamlit as st
import altair as alt
import os

# 设置页面标题
st.title("音视频观看详情")

# 读取当前目录下的音视频观看详情.xlsx文件
selected_file = '音视频观看详情.xlsx'

# 检查文件是否存在
if os.path.exists(selected_file):
    # 读取数据
    df = pd.read_excel(selected_file)

    # 清理列名，去除可能的空格
    df.columns = df.columns.str.strip()

    # 处理缺失值：将空字符串替换为 NaN
    df.replace('', pd.NA, inplace=True)

    # 获取所有可用的视频
    available_dates = df['视频'].unique()
    
    # 用户选择的视频
    selected_dates = st.multiselect("选择查看的视频", available_dates, default=available_dates)

    # 获取所有可用的课程
    available_courses = df['课程'].unique()
    
    # 用户选择的课程
    selected_courses = st.multiselect("选择查看的课程", available_courses, default=available_courses)

    # 选项：是否显示“未观看名单”
    show_unwatched_list = st.checkbox("显示未观看名单", value=False)

    if selected_dates:
        # 过滤选择的视频数据
        df_filtered = df[df['视频'].isin(selected_dates)]

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
        selected_dimension = st.selectbox("选择分析的维度", available_dimensions, index=4)  # 默认选择“授课班级”

        if selected_dimension:
            # 动态分组，按用户选择的维度进行分组
            groupby_columns = [selected_dimension]

            # 按选定维度进行合并统计：计算观看时长的总和、平均值、最大值和最小值
            watch_time_stats_by_dimension = df_filtered.groupby(groupby_columns).agg(
                总人次=('姓名', 'size'),
                总观看时长=('观看时长', 'sum'),
                最高观看时长=('观看时长', 'max'),
                最低观看时长=('观看时长', 'min'),
                已观看人次=('观看时长', lambda x: (x > 0).sum()),
                未观看人次=('观看时长', lambda x: (x == 0).sum() or (x.isna()).sum())
            ).reset_index()

            # 确保观看时长是数值格式，并且去除无效值
            watch_time_stats_by_dimension['平均观看时长'] = pd.to_numeric(watch_time_stats_by_dimension['总观看时长'], errors='coerce') / watch_time_stats_by_dimension['总人次']
            watch_time_stats_by_dimension['最高观看时长'] = pd.to_numeric(watch_time_stats_by_dimension['最高观看时长'], errors='coerce')
            watch_time_stats_by_dimension['最低观看时长'] = pd.to_numeric(watch_time_stats_by_dimension['最低观看时长'], errors='coerce')

            # 处理NaN和无效值，将它们设为0或者其他默认值
            watch_time_stats_by_dimension['平均观看时长'] = watch_time_stats_by_dimension['平均观看时长'].fillna(0)
            watch_time_stats_by_dimension['最高观看时长'] = watch_time_stats_by_dimension['最高观看时长'].fillna(0)
            watch_time_stats_by_dimension['最低观看时长'] = watch_time_stats_by_dimension['最低观看时长'].fillna(0)

            # 对数据按平均观看时长降序或升序排列
            sort_order = st.radio("选择排序方式", ('降序', '升序'), index=0)  # 默认降序
            ascending = False if sort_order == '降序' else True

            # 对数据按平均观看时长排序
            watch_time_stats_by_dimension_sorted = watch_time_stats_by_dimension.sort_values(by='平均观看时长', ascending=ascending)

            # 创建柱形图并排序
            st.subheader(f"按 {selected_dimension} 维度分析")

            # 创建柱形图，X轴为平均观看时长，Y轴为选择的维度
            bar_chart = alt.Chart(watch_time_stats_by_dimension_sorted).mark_bar().encode(
                x=alt.X('平均观看时长', sort='-x' if not ascending else 'x'),  # 确保根据升降序选择排序
                y=alt.Y(selected_dimension, sort='-x' if not ascending else 'x'),  # Y轴为维度列，按平均观看时长排序
                tooltip=[selected_dimension, '总人次', '平均观看时长', '最高观看时长', '最低观看时长', '已观看人次', '未观看人次']
            ).properties(
                title=f"{selected_dimension} 的观看时长分析"
            )

            st.altair_chart(bar_chart, use_container_width=True)

            # 构建每个维度的信息表格
            table_data = []

            for index, row in watch_time_stats_by_dimension_sorted.iterrows():
                # 查找未观看学生
                unwatched_names_str = ""
                if show_unwatched_list:
                    unwatched_students = df_filtered[ 
                        (df_filtered[selected_dimension] == row[selected_dimension]) & 
                        ((df_filtered['观看时长'].isna()) | (df_filtered['观看时长'] == 0))
                    ]

                    unwatched_names = unwatched_students['姓名'].tolist()
                    unwatched_names_str = ", ".join(unwatched_names) if unwatched_names else "没有未观看学生"

                # 将每个维度的信息添加到表格数据
                table_row = {selected_dimension: row[selected_dimension]}
                table_row.update({
                    "总人次": row['总人次'],
                    "平均观看时长": f"{row['平均观看时长']:.2f}",  # 显示平均观看时长，带两位小数
                    "最高观看时长": f"{row['最高观看时长']:.2f}",
                    "最低观看时长": f"{row['最低观看时长']:.2f}",
                    "已观看人次": row['已观看人次'],
                    "未观看人次": row['未观看人次'],
                    "未观看名单": unwatched_names_str if show_unwatched_list else ""
                })
                table_data.append(table_row)

            # 显示表格，按照平均观看时长排序
            # 强制将“平均观看时长”列的值转为数值类型，以确保正确排序
            df_table = pd.DataFrame(table_data)
            df_table['平均观看时长'] = pd.to_numeric(df_table['平均观看时长'], errors='coerce')
            st.table(df_table.sort_values(by='平均观看时长', ascending=ascending))

else:
    st.error("当前目录下没有找到'音视频观看详情.xlsx'文件。")
