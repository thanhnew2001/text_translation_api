import os

def remove_line(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    processed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if line == "":
            processed_lines.append(line)
            i += 1
            continue

        next_line_is_blank = (i + 1 < len(lines)) and (lines[i + 1].strip() == "")
        if next_line_is_blank:
            processed_lines.append(line)
        else:
            processed_lines.append(line + " ")

        i += 1

    # Join the processed lines into a single string
    processed_content = "".join(processed_lines)

    # Write the processed content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(processed_content)

remove_line("book4.txt")