# Матрица требований, реализации и доказательств

## Правила

| Требование | Реализация | Подтверждающий тест | Пробел проверки |
|---|---|---|---|
| PUB-001: RFC1918 | `RULES`, `private_v4()` | `test_all_rules_and_redaction`, `test_private_range_boundaries`, `test_documentation_ip_and_invalid_ip` | Нет полного корпуса представлений, Unicode и обфускации |
| PUB-002: .local/.internal | Regex в `RULES` | `test_all_rules_and_redaction` | Нет отдельного набора отрицательных и граничных имён |
| PUB-003: home paths | Regex в `RULES` | `test_all_rules_and_redaction` | Тест проверяет Linux-путь; отдельные macOS/Windows представления не покрыты |
| PUB-004: key headers | Regex в `RULES` | `test_all_rules_and_redaction` | Не все разновидности заголовков имеют отдельный тест |
| PUB-005: markers | `re.escape`, `re.I` | `test_all_rules_and_redaction`, `test_marker_is_literal` | Нет отдельных тестов дубликатов и кодировки политики |

## Обработка и интерфейс

| Требование | Тест | Что подтверждается | Что не подтверждается |
|---|---|---|---|
| Скрытие значений | `test_all_rules_and_redaction` | Четыре синтетических значения отсутствуют в сериализации | Полная обезличенность пути и всех контекстов |
| Чистый текст | `test_clean` | Пустые находки без пробелов | Отсутствие всех возможных секретов |
| Symlink/формат | `test_symlink_and_unsupported` | Два пробела покрытия | Race родительских каталогов, hardlink и вся матрица прав |
| Размер/кодировка/NUL | `test_size_encoding_and_binary` | Три файла дают пробелы | Все варианты ошибок декодирования и прав |
| Лимит файлов | `test_file_limit` | Возникает `file_count_limit` | Суммарный ресурсный предел |
| CLI | `test_exit_codes_and_invalid_policy` | Коды 0/1/2, пустой маркер, нулевой лимит | Все формы неверной политики и ошибки stdout |

## Доказательство CI

[Запуск 38153720204](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38153720204): девять тестов успешно выполнены для `ubuntu-latest`, `windows-latest`, `macos-latest` на head `540e1124cd2ad35f08234df589a2f07af3357dce`. Код затем слит в `6347596d5ce6e13fe3692fdcb0bf58a9fb7ceea4`.

Это свидетельство конкретного набора тестов на hosted runners. Оно не заменяет проверку пользовательской среды, измерение точности на корпусе или тест эксплуатации реальных документов. Для каждого нового обещания поддержки матрица должна расширяться тестом и результатом.

---

[Оглавление документации](index.md) · [English](../en/check-matrix.md)
