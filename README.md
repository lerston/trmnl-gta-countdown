# GTA VI Countdown for TRMNL

Неофициальный полноэкранный countdown до GTA VI для TRMNL OG 2-bit 800 × 480. Liquid-шаблон показывает число дней, меняет фон по московской дате и оставляет цифры и логотип отдельными контрастными слоями.

## Возможности

- компактный production-шаблон без встроенных Base64-ресурсов;
- ежедневный воспроизводимый выбор одного из четырёх фонов;
- Montserrat ExtraBold и монохромный SVG-логотип;
- режим TRMNL Black & White с серверным дизерингом фона;
- автономный локальный preview и проверки дат, ротации и ограничения 100 KB.

## Быстрый старт

1. Создайте Private Plugin со стратегией **Static**.
2. В **Static Data** вставьте содержимое [`static-data.json`](static-data.json).
3. В **Edit Markup → Full** полностью вставьте [`full.liquid`](full.liquid).
4. Установите **Remove bleed margin: Yes** и **Dark Mode: No**.
5. Добавьте плагин в Playlist на полный экран и выполните **Force Refresh**.

Для точечного чёрно-белого фона выберите **Presentation → Black & White (1-bit)**. Дизеринг выполняется сервером TRMNL, поэтому локальный preview показывает только оттенки серого.

## Локальная сборка и проверка

Требуется Python 3.12 или новее.

```text
python build.py
```

Команда пересобирает `full.liquid`, монохромный логотип и исключённый из Git `preview.html`. Она также проверяет шесть граничных дат, ротацию для разного числа изображений и размер production-шаблона. CI повторяет сборку и не допускает незакоммиченные изменения сгенерированных production-файлов.

Подробности реализации, ограничения TRMNL и источники: [`docs/implementation.md`](docs/implementation.md).

## Добавление фонов

Добавьте PNG в `assets/` с именем `art-NN.png`, запустите `python build.py`, затем добавьте raw-ссылку в массив `artworks` файла `static-data.json`. Фактический 1-bit результат необходимо проверить на устройстве.

## Права и лицензии

Проект не связан с Rockstar Games. Права на GTA VI, логотип и иллюстрации принадлежат соответствующим правообладателям. Собственный код распространяется по MIT License; сторонние материалы исключены из неё и перечислены в [`ASSET_LICENSES.md`](ASSET_LICENSES.md). Montserrat распространяется по SIL Open Font License из [`assets/OFL.txt`](assets/OFL.txt).

Правила изменений, pull request и выпуска описаны в [`CONTRIBUTING.md`](CONTRIBUTING.md).
