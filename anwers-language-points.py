# 构建每个维度的信息表格
table_data = []

for index, row in attendance_by_dimension_sorted.iterrows():
    # 查找答错学生
    absent_names_str = ""
    if show_absent_students:
        absent_students = df_filtered[ 
            (df_filtered[selected_dimension] == row[selected_dimension]) & 
            (df_filtered['答题情况'] == '错误')  # 确保这里是筛选答错的学生
        ]

        absent_names = absent_students['姓名'].tolist()
        
        if absent_names:  # 如果有答错学生
            absent_names_str = ", ".join(absent_names)
        else:  # 如果没有答错学生
            absent_names_str = "所有学生都已经答对"

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
