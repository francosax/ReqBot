import configparser
import os


def load_keyword_config():
    word_set = {}
    # Insieme di parole predefinito
    default_word_set = {'must', 'shall', 'should', 'has to', 'scope', 'recommended', 'ensuring', 'ensures', 'ensure'}

    # Percorso del file di configurazione
    config_file_path = 'RBconfig.ini'

    # Verifica se il file esiste
    if not os.path.exists(config_file_path):
        # Crea un nuovo file di configurazione con i valori predefiniti
        config = configparser.ConfigParser()
        config['DEFAULT_KEYWORD'] = {'word_set': ','.join(default_word_set)}

        # Scrive il file di configurazione
        with open(config_file_path, 'w') as configfile:
            config.write(configfile)

        # Popola word_set con i valori predefiniti
        word_set = default_word_set
    else:
        # Leggi il file di configurazione esistente
        config = configparser.ConfigParser()
        try:
            config.read(config_file_path)

            # Ottieni l'insieme di parole dal file di configurazione
            word_set_str = config.get('DEFAULT_KEYWORD', 'word_set')
            word_set = set(word_set_str.split(','))

            # Filtra gli elementi vuoti
            word_set = {word for word in word_set if word.strip()}

            if not word_set:  # Verifica se word_set è vuoto dopo la rimozione degli elementi vuoti
                print("Il file di configurazione non contiene parole valide. Riscrivere con i valori predefiniti.")
                # Riscrivi il file di configurazione con i valori predefiniti
                config['DEFAULT_KEYWORD'] = {'word_set': ','.join(default_word_set)}
                with open(config_file_path, 'w') as configfile:
                    config.write(configfile)
            else:
                print(f"Parole lette dal file di configurazione: {word_set}")
        except configparser.Error:  # Cattura eventuali errori di lettura del file di configurazione
            print("Il file di configurazione è danneggiato. Riscrivere con i valori predefiniti.")
            # Riscrivi il file di configurazione con i valori predefiniti
            config['DEFAULT_KEYWORD'] = {'word_set': ','.join(default_word_set)}
            with open(config_file_path, 'w') as configfile:
                config.write(configfile)

    return word_set
