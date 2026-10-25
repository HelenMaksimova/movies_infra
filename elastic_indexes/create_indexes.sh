#!/bin/bash

ES_HOST="${ES_HOST:-elasticsearch}"
ES_PORT="${ES_PORT:-9200}"
SCHEMAS_DIR="${SCHEMAS_DIR:-/schemas}"

index_exists() {
    local index_name=$1
    curl -s -f -o /dev/null "http://${ES_HOST}:${ES_PORT}/${index_name}"
    return $?
}

create_index() {
    local index_name=$1
    local schema_file=$2

    echo "Проверка индекса ${index_name}..."

    if index_exists "${index_name}"; then
        echo "✓ Индекс ${index_name} уже существует"
        return 0
    fi

    echo "Создание индекса ${index_name}..."

    if curl -s -f -X PUT "http://${ES_HOST}:${ES_PORT}/${index_name}" \
        -H 'Content-Type: application/json' \
        -d @"${schema_file}" > /dev/null; then
        echo "✓ Индекс ${index_name} успешно создан"
        return 0
    else
        echo "✗ Ошибка при создании индекса ${index_name}"
        return 1
    fi
}

echo "Ожидание запуска Elasticsearch..."
until curl -s "http://${ES_HOST}:${ES_PORT}/_cluster/health" | grep -q '"status":"\(green\|yellow\)"'; do
    echo "Ожидание Elasticsearch..."
    sleep 2
done
echo "✓ Elasticsearch готов к работе"

echo "Поиск файлов схем в ${SCHEMAS_DIR}..."
schema_files=$(find "${SCHEMAS_DIR}" -name "*_schema.json" -type f)

if [ -z "${schema_files}" ]; then
    echo "⚠ Файлы схем не найдены в ${SCHEMAS_DIR}"
    exit 0
fi

# Создание индексов
failed_indices=()
success_count=0

for schema_file in ${schema_files}; do
    # Извлечение имени индекса из имени файла (удаляем _schema.json)
    filename=$(basename "${schema_file}")
    index_name="${filename%_schema.json}"

    if create_index "${index_name}" "${schema_file}"; then
        ((success_count++))
    else
        failed_indices+=("${index_name}")
    fi
done

echo "========================================="
echo "Результат создания индексов:"
echo "Успешно создано/проверено: ${success_count}"
if [ ${#failed_indices[@]} -gt 0 ]; then
    echo "Не удалось создать: ${failed_indices[*]}"
    exit 1
else
    echo "Все индексы успешно обработаны"
    exit 0
fi