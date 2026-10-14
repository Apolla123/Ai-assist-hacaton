import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import parser
from docx import Document


print('Просмотр новостей...')
parser.ParseAndSave()

FILE_NAME = "news.json"
model = SentenceTransformer("BAAI/bge-m3")


def load_news(file_name: str = FILE_NAME) -> list[dict]:
    # Загружает статьи из JSON-файла.
    with open(file_name, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def calculate_relevance(news_text, user_preferences):
    # Считаем настолько подходят теги под запрос
    texts = [user_preferences, news_text]
    embeddings = model.encode(texts, normalize_embeddings=True)

    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    return float(score)


def main():
    # Основной код
    user_tags = input('Напиши что тебе интересно: ')
    data = load_news(FILE_NAME)

    digest_content = []

    while data:
        list_news = []

        # Ищем первую подходящую новость
        for article in data:
            title = article.get("title", "")
            description = article.get("description", "")
            tags = article.get("category", "")
            date = article.get("date", "")
            link = article.get("link", "")

            # Объединяем все текстовые поля в одну строку
            full_text = f"{title} {description} {tags}"

            score = calculate_relevance(full_text, user_tags)

            list_news.append({'title': title,
                              'date': date,
                              'link': link,
                              'score': score,
                              'article': article})

        list_news = sorted(list_news, key=lambda x: x['score'], reverse=True)[:5]
        digest_content.append({'tags': user_tags, 'news': list_news})
        user_tags = input('Напиши что тебе интересно: ')

        if user_tags == 'Всё' or user_tags == '':
            break

        # Удаляем показанные новости из основного списка
        shown_ids = {id(item['article']) for item in list_news}
        data = [article for article in data if id(article) not in shown_ids]

    # Экспорт в DOCX
    export_to_docx(digest_content)


def export_to_docx(digest_content, filename="digest.docx"):
    doc = Document()

    # Заголовок
    doc.add_heading('Дайджест новостей', 0)

    for entry in digest_content:
        # Тема
        doc.add_heading(f"Тема: {entry['tags']}", level=1)

        # Новости
        for i, news in enumerate(entry['news'], 1):
            p = doc.add_paragraph()
            p.add_run(f"{i}. ").bold = True
            p.add_run(news['title']).bold = True

            doc.add_paragraph(f"   - Дата: {news['date']}", style='List Bullet')
            doc.add_paragraph(f"   - Ссылка: {news['link']}", style='List Bullet')

            score = news['score']

            if score >= 0.35:
                proiriti = 'Высокий'
            elif score >= 0.25:
                proiriti = 'Средний'
            else:
                proiriti = 'Низкий'

            doc.add_paragraph(f"   - Приоритет: {proiriti}", style='List Bullet')

    doc.save(filename)
    print(f"DOCX файл сохранён: {filename}")


if __name__ == "__main__":
    main()