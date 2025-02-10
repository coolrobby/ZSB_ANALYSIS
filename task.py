import pandas as pd
import streamlit as st
import altair as alt
import os

# 设置页面标题
st.title("2025专升本作业统计-英语")

# 获取当前目录下“作业统计”子文件夹路径
assignments_folder = os.path.join(os.getcwd(), "作业统计")

# 检查文件夹是否存在
if os.path.exists(assignments_folder):
    # 获取所有的xlsx文件，不包括扩展名
    xlsx_files = [f.split('.')[0] for f in os.listdir(assignments_folder) if f.endswith('.xlsx')]

    # 如果没有xlsx文件
    if not xlsx_files:
        st.error("在‘作业统计’文件夹中没有找到任何xlsx文件。")
    else:
        # 用户选择文件，默认选择第一个文件
        selected_file = st.multiselect("选择要分析的文件", xlsx_files, default=xlsx_files[:1])

        if selected_file:
            # 构建文件路径
            selected_file_path = os.path.join(assignments_folder, f"{selected_file[0]}.xlsx")
            
            # 读取数据
            df = pd.read_excel(selected_file_path)

            # 清理列名，去除可能的空格
            df.columns = df.columns.str.strip()

            # 处理缺失值：将空字符串替换为 NaN
            df.replace('', pd.NA, inplace=True)

            # 如果成绩为空，视为缺考
            df['成绩'] = df['成绩'].fillna('缺考')

            # 获取所有可用的作业
            available_dates = df['作业'].unique()
            selected_dates = st.multiselect("选择查看的作业", available_dates, default=available_dates)

            # 获取所有可用的课程
            available_courses = df['课程'].unique()
            selected_courses = st.multiselect("选择查看的课程", available_courses, default=available_courses)

            if selected_dates:
                # 过滤选择的作业数据
                df_filtered = df[df['作业'].isin(selected_dates)]

                # 如果用户选择了课程，则过滤课程
                if selected_courses:
                    df_filtered = df_filtered[df_filtered['课程'].isin(selected_courses)]

                # 获取所有可用的维度（列名）
                available_dimensions = ['学校', '院系', '专业', '行政班级', '授课班级', '教师']
                if selected_courses:
                    available_dimensions.append('课程')

                # 用户选择的维度
                selected_dimension = st.selectbox("选择分析的维度", available_dimensions, index=1)  # 默认选择“院系”

                if selected_dimension:
                    # 选择是否显示缺考名单（默认不显示）
                    show_absent_list = st.checkbox("显示缺考名单", value=False)

                    # 按选定维度分组，计算各项统计数据
                    stats_by_dimension = df_filtered.groupby([selected_dimension]).agg(
                        总人次=('姓名', 'size'),
                        平均成绩=('成绩', lambda x: pd.to_numeric(x[x != '缺考'], errors='coerce').mean()),  # 排除缺考
                        及格人次=('成绩', lambda x: (pd.to_numeric(x[x != '缺考'], errors='coerce') >= 60).sum()),
                        实考人次=('成绩', lambda x: (x != '缺考').sum()),
                        缺考人次=('成绩', lambda x: (x == '缺考').sum()),
                        缺考名单=('姓名', lambda x: ", ".join(x[df_filtered['成绩'] == '缺考'])),  # 计算缺考名单
                        最高分=('成绩', lambda x: pd.to_numeric(x[x != '缺考'], errors='coerce').max()),
                        最低分=('成绩', lambda x: pd.to_numeric(x[x != '缺考'], errors='coerce').min()),
                        分数段0_59=('成绩', lambda x: ((pd.to_numeric(x[x != '缺考'], errors='coerce') < 60).sum())),
                        分数段60_69=('成绩', lambda x: ((pd.to_numeric(x[x != '缺考'], errors='coerce') >= 60) & (pd.to_numeric(x[x != '缺考'], errors='coerce') < 70)).sum()),
                        分数段70_79=('成绩', lambda x: ((pd.to_numeric(x[x != '缺考'], errors='coerce') >= 70) & (pd.to_numeric(x[x != '缺考'], errors='coerce') < 80)).sum()),
                        分数段80_89=('成绩', lambda x: ((pd.to_numeric(x[x != '缺考'], errors='coerce') >= 80) & (pd.to_numeric(x[x != '缺考'], errors='coerce') < 90)).sum()),
                        分数段90_99=('成绩', lambda x: ((pd.to_numeric(x[x != '缺考'], errors='coerce') >= 90) & (pd.to_numeric(x[x != '缺考'], errors='coerce') < 100)).sum()),
                        分数段100=('成绩', lambda x: (pd.to_numeric(x[x != '缺考'], errors='coerce') == 100).sum())
                    ).reset_index()

                    # 处理NaN值
                    stats_by_dimension.fillna(0, inplace=True)

                    # 计算及格率
                    stats_by_dimension['及格率'] = (stats_by_dimension['及格人次'] / stats_by_dimension['实考人次'] * 100).fillna(0).round(2)

                    # 选择排序方式
                    ascending = st.radio("选择排序方式", ('降序', '升序'), index=0)

                    # 按“平均成绩”排序
                    stats_by_dimension_sorted = stats_by_dimension.sort_values(by='平均成绩', ascending=(ascending == '升序'))

                    # 显示柱形图
                    st.subheader(f"按 {selected_dimension} 维度分析")

                    bar_chart = alt.Chart(stats_by_dimension_sorted).mark_bar().encode(
                        x=alt.X('平均成绩', sort='-x' if ascending == '降序' else 'x'),
                        y=alt.Y(selected_dimension, sort='-x' if ascending == '降序' else 'x'),
                        tooltip=[selected_dimension, '总人次', '平均成绩', '及格人次', '实考人次', '缺考人次', '最高分', '最低分',
                                 '分数段0_59', '分数段60_69', '分数段70_79', '分数段80_89', '分数段90_99', '分数段100']
                    ).properties(
                        title=f"{selected_dimension} 的成绩分析"
                    )

                    st.altair_chart(bar_chart, use_container_width=True)

                    # 构建表格
                    table_data = []
                    for _, row in stats_by_dimension_sorted.iterrows():
                        table_row = {
                            selected_dimension: row[selected_dimension],
                            "总人次": row['总人次'],
                            "平均成绩": f"{row['平均成绩']:.2f}",
                            "及格人次": row['及格人次'],
                            "及格率": f"{row['及格率']:.2f}%",
                            "实考人次": row['实考人次'],
                            "缺考人次": row['缺考人次'],
                            "最高分": f"{row['最高分']:.2f}",
                            "最低分": f"{row['最低分']:.2f}",
                            "分数段0_59": row['分数段0_59'],
                            "分数段60_69": row['分数段60_69'],
                            "分数段70_79": row['分数段70_79'],
                            "分数段80_89": row['分数段80_89'],
                            "分数段90_99": row['分数段90_99'],
                            "分数段100": row['分数段100']
                        }

                        # 只有当用户勾选“显示缺考名单”时，才添加缺考名单列
                        if show_absent_list:
                            table_row["缺考名单"] = row['缺考名单']

                        table_data.append(table_row)

                    df_table = pd.DataFrame(table_data)
                    df_table['平均成绩'] = pd.to_numeric(df_table['平均成绩'], errors='coerce')
                    st.table(df_table.sort_values(by='平均成绩', ascending=(ascending == '升序')))
        else:
            st.error("请至少选择一个文件进行分析。")
else:
    st.error("当前目录下没有找到‘作业统计’子文件夹。")
