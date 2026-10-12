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
| Symlink/формат | `test_symlink_and_unsupported` | Пробелы symlink/формата и пустая область | Race родительских каталогов, hardlink и вся матрица прав |
| Размер/кодировка/NUL | `test_size_encoding_and_binary` | Три файла дают пробелы | Все варианты ошибок декодирования и прав |
| Лимит файлов | `test_file_limit` | Возникает `file_count_limit` | Суммарный ресурсный предел |
| CLI | `test_exit_codes_and_invalid_policy` | Коды 0/1/2, пустой маркер, нулевой лимит | Все формы неверной политики и ошибки stdout |

## Доказательство CI

[Запуск 38153720204](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38153720204): девять тестов успешно выполнены для `ubuntu-latest`, `windows-latest`, `macos-latest` на head `540e1124cd2ad35f08234df589a2f07af3357dce`. Код затем слит в `6347596d5ce6e13fe3692fdcb0bf58a9fb7ceea4`.

Это свидетельство конкретного набора тестов на hosted runners. Оно не заменяет проверку пользовательской среды, измерение точности на корпусе или тест эксплуатации реальных документов. Для каждого нового обещания поддержки матрица должна расширяться тестом и результатом.

## Регрессии усиления в 0.2

| Область | Методы тестов | Свидетельство |
|---|---|---|
| Покрытие | `test_exact_env`, `test_empty_scope`, `test_exclusions_visible` | Точный `.env` проверен; пустой и исключённый вход не считается чистым |
| Байты | `test_total_bytes_limit_and_exact_boundary`, `test_invalid_files_consume_byte_budget` | Общий предел, точная граница, учёт неверного входа |
| Находки | `test_finding_limit_and_exact_boundary` | Допустимые находки сохранены; превышение явно отражено |
| Обход | `test_directory_limit` | Корень учитывается; избыточное ветвление останавливает обход |
| Политика | `test_policy_utf8`, `test_policy_unknown_and_duplicate_fields`, `test_policy_limits_and_duplicate_markers` | Кириллица, неизвестные/повторные ключи, неверный корень, пределы байт/маркеров |
| API | `test_positive_integer_api_limits` | Нулевой, отрицательный, boolean и нецелый бюджет отвергаются |
| Позиция | `test_newline_line_numbers` | Номера строк повторных маркеров корректны |
| CLI | `test_cli_empty_unknown_utf8_and_limits` | Коды для пустой области, кириллицы, опечатки и бюджета |

Набор сканера содержит 22 тестовых метода. Они проверяют синтетические сценарии, а не исчерпывающую точность правил, устойчивость к гонкам или предел общей памяти процесса.

## Проверка предыдущего усиления

Все 22 теста прошли на Linux, Windows и macOS с Python 3.13 в [запуске 38155720812](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38155720812) на head реализации `197f07d563b25193c86ab011e8bfd0798e005bc1`. Ссылки, соответствие языковых версий и пример руководства проверены локально.

## Контракт и проверка потребителя

| Требование | Тесты | Свидетельство и ограничение |
|---|---|---|
| Стандартная схема | `test_schema_and_labeled_fixtures` | Проверка метасхемой; 15 размеченных ответов; это не полный корпус обнаружения |
| Совместимость производителя | `test_live_scanner_outputs` | Принимается реальный вывод для пустого входа/.env/бюджетов/кодировок/дерева |
| Строгая структура | `test_required_fields_and_unknown_envelopes`, `test_schema_types_and_unknown_fields`, `test_finding_shape_redaction_and_static_rule_mapping`, `test_gap_assets_and_unknown_reasons` | Отвергаются пропущенные/лишние поля, boolean, неверные правила, открытые evidence и пути пробелов |
| Согласованность | `test_coverage_and_empty_scope_consistency`, `test_stop_state_consistency`, `test_budget_and_counter_consistency` | Условия покрытия, счётчиков и остановки; подлинность источника не доказана |
| Ресурсы и вход | `test_error_cap_and_numeric_integer_semantics`, `test_strict_json_and_read_boundaries`, `test_symlink_and_special_file_rejection` | Пределы ошибок/чтения/глубины, строгий JSON; это не песочница процесса |
| Безопасное выполнение | `test_no_network_during_validation`, `test_cli_result_codes_and_safe_errors`, `test_unavailable_schema_fails_closed` | Для поставляемой схемы нет сетевой попытки; коды 0–3; без зависимости/схемы успеха нет |
| Двуязычные примеры | `check_docs.py` | Локальные ссылки, 17 пар страниц, совпадение команд и запуск примеров сканера/валидатора |

Полный набор содержит 37 методов. Точная семантика потребителя — в [руководстве валидатора](report-validation.md).

## Текущая проверка: 0.2.0a2

Все 37 тестовых методов, `pip check` и `check_docs.py` прошли на Linux, Windows и macOS с Python 3.13 в [запуске 38156874002](https://github.com/mejustbox-byte/publication-opsec-guard/actions/runs/38156874002) на head реализации/документации `5fb0da0e6f67e2898b4cb1877cb68ae76a0e8f9b`. Проверены установка зависимостей, 17 пар страниц RU/EN и выполняемые примеры; это не доказательство совместимости Intel Mac или подлинности источника.

---

[Оглавление документации](index.md) · [English](../en/check-matrix.md)


## Доказательства области alpha

Тесты выпуска добавляют XLSX-представления, смешанный/документный запуск, неподдержанную/пустую/ссылочную область, отказ запрошенного движка, общие лимиты и согласованность вложенных ответов. Аудит: [фиксированные зависимости валидатора](../evidence/validation-dependency-audit-2026-10-12.json). Это конечные синтетические проверки, не полнота поиска секретов/рендеринг Office.
