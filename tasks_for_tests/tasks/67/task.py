def replace_one_with_word(s: str) -> str:    """Заменяет все цифры 1 на слово one."""    return s.replace('1', 'one')

if __name__ == "__main__":    print(replace_one_with_word(input()))