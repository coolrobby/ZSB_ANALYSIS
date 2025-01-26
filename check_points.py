# 计算完成率，并确保其为数值格式
def safe_calculate_rate(row):
    try:
        return (row['已完成人次'] / row['总人次']) * 100
    except ZeroDivisionError:  # 处理除以0的情况
        return 0  # 或者返回一个默认值，例如0
    except Exception as e:
        return None  # 如果出现其他错误，返回缺失值

# 应用安全的完成率计算
attendance_by_dimension['完成率'] = attendance_by_dimension.apply(safe_calculate_rate, axis=1)

# 转换为数值格式，确保完成率是数字
attendance_by_dimension['完成率数值'] = pd.to_numeric(attendance_by_dimension['完成率'], errors='coerce')

# 创建一个新的列，确保完成率为 100% 的数据排在前面
attendance_by_dimension['排序完成率'] = attendance_by_dimension['完成率数值'].apply(lambda x: -1 if x == 100 else x)

# 对数据按完成率降序或升序排列
sort_order = st.radio("选择排序方式", ('降序', '升序'), index=0)  # 默认降序
ascending = False if sort_order == '降序' else True

# 对数据按完成率排序，使用数值格式的列进行排序
attendance_by_dimension_sorted = attendance_by_dimension.sort_values(by=['排序完成率', '完成率数值'], ascending=[True, ascending])

# 创建柱形图并排序
st.subheader(f"按 {selected_dimension} 维度分析")

# 创建柱形图，X轴为完成率，Y轴为选择的维度
bar_chart = alt.Chart(attendance_by_dimension_sorted).mark_bar().encode(
    x=alt.X('完成率数值', sort='-x' if not ascending else 'x'),  # 确保根据升降序选择排序
    y=alt.Y(selected_dimension, sort='-x' if not ascending else 'x'),  # Y轴为维度列，按完成率排序
    tooltip=[selected_dimension, '总人次', '已完成人次', '未完成人次', '完成率数值']
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
        "完成率": f"{row['完成率数值']:.2f}",  # 显示完成率为数字，带两位小数
        "未完成人次": row['未完成人次'],
        "未完成学生": absent_names_str if show_absent_students else ""
    })
    table_data.append(table_row)

# 显示表格，按完成率排序
st.table(pd.DataFrame(table_data).sort_values(by='完成率数值', ascending=ascending))
