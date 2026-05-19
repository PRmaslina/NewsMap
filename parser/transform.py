import json

from placeFinder import init_news_finder


# ============================================================
# INIT MODEL
# ============================================================

finder = init_news_finder()


# ============================================================
# LOAD SOURCE JSON
# ============================================================

with open("json_data/News_with_positions_precise.json","r",encoding="utf-8") as f:

    news_data = json.load(f)


# ============================================================
# RESULT DATASET
# ============================================================

train_dataset = []


# ============================================================
# PROCESS NEWS
# ============================================================

for news in news_data:

    title = news.get("title", "")

    subtitle = news.get("subTitle", "")

    text = news.get("text", "")

    true_position = (
        news.get("position", "")
        .strip()
        .lower()
    )

    # --------------------------------------------------------
    # EXTRACT ENTITIES
    # --------------------------------------------------------

    entities = finder.extract_entities(
        title,
        subtitle,
        text
    )

    # --------------------------------------------------------
    # CREATE TRAIN RECORDS
    # --------------------------------------------------------

    for entity in entities:

        entity_name = (
            entity["entity_name"]
            .strip()
            .lower()
        )

        entity_normal = (
            entity["entity_normal"]
            .strip()
            .lower()
        )

        # ----------------------------------------------------
        # LABEL
        # ----------------------------------------------------

        label = 0

        # точное совпадение
        if true_position in entity_name:
            label = 1

        elif entity_name in true_position:
            label = 1

        elif true_position in entity_normal:
            label = 1

        elif entity_normal in true_position:
            label = 1

        # ----------------------------------------------------
        # FINAL OBJECT
        # ----------------------------------------------------

        train_item = {

            "entity_type": entity["entity_type"],

            "entity_name": entity["entity_name"],

            "entity_normal": entity["entity_normal"],

            "data": entity["data"],

            "label": label
        }

        train_dataset.append(train_item)


# ============================================================
# SAVE TRAIN.JSON
# ============================================================

with open(
    "json_data/train.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        train_dataset,
        f,
        ensure_ascii=False,
        indent=4
    )

print("train.json CREATED")
print("TOTAL SAMPLES:", len(train_dataset))