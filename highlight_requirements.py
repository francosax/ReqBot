import fitz


def highlight_requirements(filepath, requirements_list, note_list, page_list, out_pdf_name):
    # Funzione per trovare tutte le posizioni di una parola in una lista di parole
    def find_all_positions(word, words):
        return [i for i, w in enumerate(words) if w[4] == word]

    def find_consecutive_sequence(words, sequence):
        for i in range(len(words)):
            current_sequence = []
            for j in range(i, len(words)):
                if len(current_sequence) < len(sequence) and words[j][4] == sequence[len(current_sequence)]:
                    current_sequence.append(words[j])
                else:
                    break
            if len(current_sequence) == len(sequence):
                return current_sequence
        return []

    # special_string = ['\u202f', '\u200b', '\u2014', '\t']
    # def find_consecutive_sequence(words, sequence):
    #     for i in range(len(words)):
    #         current_sequence = []
    #         for j in range(i, len(words)):
    #
    #             parola_da_trovare = words[j][4]
    #             risultato_check = any(carattere in parola_da_trovare for carattere in special_string)
    #
    #             if risultato_check:
    #                 # Se è presente almeno un carattere speciale, procedi con la rimozione
    #                 for carattere in special_string:
    #                     parola_da_trovare = parola_da_trovare.replace(carattere, "")
    #
    #             if len(current_sequence) < len(sequence) and parola_da_trovare == sequence[len(current_sequence)]:
    #                 current_sequence.append(words[j])
    #             else:
    #                 break
    #         if len(current_sequence) == len(sequence):
    #             return current_sequence
    #     return []

    doc = fitz.open(filepath)

    for i in range(len(requirements_list)):

        sentence_parts = requirements_list[i]
        # for page_number in range(len(doc)):

        pagina = page_list[i] - 1
        page = doc[pagina]
        words = page.get_text("words")  # Ottieni parole con le loro posizioni
        # print(words)

        positions = [find_all_positions(part, words) for part in sentence_parts]
        found_sequence = find_consecutive_sequence(words, sentence_parts)

        if found_sequence:
            # Calcola i limiti del rettangolo di evidenziazione
            min_x = min(word[0] for word in found_sequence)
            min_y = min(word[1] for word in found_sequence)
            max_x = max(word[2] for word in found_sequence)
            max_y = max(word[3] for word in found_sequence)
            # print(str(pagina)+":",str(min_x)+";",str(min_y)+";",str(max_x)+";",str(max_y))
            # Crea il rettangolo di evidenziazione
            highlight_rect = fitz.Rect(min_x, min_y, max_x, max_y)

            # Aggiungi l'annotazione di evidenziazione alla pagina
            highlight = page.add_highlight_annot(highlight_rect)
            highlight.update()

            # Aggiungi una nota alla pagina
            note_text = note_list[i]
            point = fitz.Point(max_x, min_y)
            page.add_text_annot(point, note_text)

    doc.save(out_pdf_name, encryption=fitz.PDF_ENCRYPT_KEEP)
