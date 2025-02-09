# 允许用户选择是否显示缺考名单，默认不显示
show_absent_list = st.checkbox("显示缺考名单", value=False)

# 构建每个维度的信息表格
table_data = []

for index, row in stats_by_dimension_sorted.iterrows():
    # 将每个维度的信息添加到表格数据
    table_row = {selected_dimension: row[selected_dimension]}
    table_row.update({
        "总人次": row['总人次'],
        "平均成绩": f"{row['平均成绩']:.2f}",  # 显示平均成绩，带两位小数
        "及格人次": row['及格人次'],
        "及格率": f"{row['及格率']:.2f}%",  # 显示及格率，带百分号
        "实考人次": row['实考人次'],
        "缺考人次": row['缺考人次'],
        "最高分": f"{row['最高分']:.2f}",  # 显示最高分，带两位小数
        "最低分": f"{row['最低分']:.2f}",  # 显示最低分，带两位小数
        "分数段0_59": row['分数段0_59'],
        "分数段60_69": row['分数段60_69'],
        "分数段70_79": row['分数段70_79'],
        "分数段80_89": row['分数段80_89'],
        "分数段90_99": row['分数段90_99'],
        "分数段100": row['分数段100']
    })
    
    # 仅当用户勾选“显示缺考名单”时，才添加缺考名单列
    if show_absent_list:
        table_row["缺考名单"] = row['缺考名单']

    table_data.append(table_row)

# 显示表格，按照平均成绩排序
df_table = pd.DataFrame(table_data)
df_table['平均成绩'] = pd.to_numeric(df_table['平均成绩'], errors='coerce')
st.table(df_table.sort_values(by='平均成绩', ascending=(ascending == '升序')))
