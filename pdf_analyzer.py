import logging

import en_core_web_sm
import fitz
import pandas as pd

logging.basicConfig(filename='debug.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


def requirement_finder(path, keywords_set, filename):
    doc = fitz.open(path)
    nlp = en_core_web_sm.load()

    cont_text = []
    pagine = []
    keyword = []

    for i, page in enumerate(doc, 1):
        page_text = page.get_text()
        # print(text)
        cont_text.append(page_text)

    # word_set = keywords_set
    word_set = {word.lower() for word in keywords_set}

    raw_sentences = []
    matching_sentences = []
    tag = []
    req_c = 0
    # position = []
    current_page = None

    for i, page_text in enumerate(cont_text, 1):
        if i != current_page:
            req_c = 0
            current_page = i

        lines = page_text.splitlines()
        lines = [line for line in lines if line.strip() != '']
        filtered_text = '\n'.join(lines)
        doc_page = nlp(filtered_text)
        for sent in doc_page.sents:

            if any(word.lower() in word_set for word in sent.text.split()):
                req_c += 1
                # raw_sentences.append(sent)
                raw_sentences.append(sent.text.split())
                cleaned_sentence = sent.text.strip().replace('\n', ' ')
                matching_sentences.append(cleaned_sentence)
                pagine.append(i)
                # Find the keyword and ensure it's in lowercase
                keyword_word = next(word.lower() for word in sent.text.split() if word.lower() in word_set)
                keyword.append(keyword_word)
                # Create a tag for the requirement
                tag.append(filename + '-Req#' + str(i) + '-' + str(req_c))

    df = pd.DataFrame({
        'Label Number': tag,
        'Description': matching_sentences,
        'Page': pagine,
        'Keyword': keyword,
        'Raw': raw_sentences
        # 'position_for_note': position
    })

    df['Priority'] = df['Description'].apply(lambda x: 'high' if 'must' in x.lower() or 'shall' in x.lower()
    else 'medium' if 'should' in x.lower() or 'has to' in x.lower()
    else 'security' if 'security' in x.lower()
    else 'low')

    lista_note = []
    for j in range(len(df['Label Number'])):
        lista_note.append(df['Label Number'][j] + ":" + df['Description'][j])
    df['Note'] = lista_note

    return df
