def main():
    import pandas as pd
    from googletrans import Translator
    import nltk
    import spacy
    import re
    from word2number import w2n
    from IPython.display import display, HTML, Javascript
    from spacy import displacy
    pd.set_option('display.max_columns', 7)
    pd.set_option('display.max_rows', 1000)
    pd.options.display.max_colwidth = 1000
    pd.options.mode.chained_assignment = None

    colors = {'FOOD': 'linear-gradient(90deg, #aa9cfc, #fc9ce7)',
              'VOLVAL': 'linear-gradient(180deg, #f920eb, #4957ed)',
              'VOLENT': 'linear-gradient(90deg, #72db4c, #17ecef)',
              'QUA': 'linear-gradient(45deg, #0050ff, #fff600)'}
    options = {'ents': ['FOOD', 'QUA', 'VOLVAL', 'VOLENT'], 'colors': colors}

    def re_pattern_finder(pattern, in_str, result_list):
        result = re.findall(pattern, in_str)
        # clear_wo_patterns = re.sub(pattern, "", in_str)
        if len(result) > 0:
            result_list += result
        # return clear_wo_patterns

    def capacity_detect(tokens):
        # print(tokens)
        capacity_element_list = list()
        capacity_index_list = list()
        tok_str = ' '.join(tokens)
        gram_mll_patt = re.compile(r"\d+\sg\b|\d+\sgr\b|\d+\sml\b|\d+g\b|\d+gr\b|\d+ml\b")
        # number_x_patt = re.compile(r"\d+x")

        re_pattern_finder(gram_mll_patt, tok_str, capacity_element_list)
        for element in capacity_element_list:
            part_element = element.split(' ')
            # print('part element', part_element)
            # print(len(part_element))
            if len(part_element) == 1:
                capacity_index_list.append(tokens.index(part_element[0]))
            elif len(part_element) > 1:
                buff_index = list()
                for part in part_element:
                    buff_index.append(tokens.index(part))
                buff_index.sort(key=int)
                # print(buff_index)
                for el in range(len(buff_index) - 1):
                    if buff_index[el + 1] - buff_index[el] == 1:
                        capacity_index_list.append(buff_index[el])
        return capacity_index_list
        # print(tok_str)
        # print(capacity_index_list)
        # print(capacity_element_list)
        # tok_str = re_pattern_finder(number_x_patt, tok_str, capacity_index_list)

    def quantity_detect(tokens, ignore_index):  # , str_wo_capacity
        quantity_index_list = list()
        quantity_element_list = list()
        tok_str = ' '.join(tokens)

        number_x_patt = re.compile(r"\d+\b|\d+\sx\b|\d+x\b")

        re_pattern_finder(number_x_patt, tok_str, quantity_element_list)

        for element in quantity_element_list:
            part_element = element.split(' ')
            # print('part element', part_element)
            # print(len(part_element))
            if len(part_element) == 1:
                part_index = tokens.index(part_element[0])
                if part_index not in ignore_index:
                    quantity_index_list.append(part_index)
            elif len(part_element) > 1:
                buff_index = list()
                for part in part_element:
                    buff_index.append(tokens.index(part))
                buff_index.sort(key=int)
                # print(buff_index)
                for el in range(len(buff_index) - 1):
                    if buff_index[el + 1] - buff_index[el] == 1:
                        if buff_index[el] not in ignore_index:
                            quantity_index_list.append(buff_index[el])
        return list(set(quantity_index_list))

    def tare_detect(tokens, tare_dict):
        tare_entity = dict()
        for token in tokens:
            if token in tare_dict:
                tare_entity[tokens.index(token)] = tare_dict[token]
        return tare_entity

    def food_entity_detect(tokens, food_list):
        food_entity_index = list()
        for token in tokens:
            try:
                food_list.index(token)
            except ValueError:
                pass
            else:
                # print(token)
                food_entity_index.append(tokens.index(token))
        return food_entity_index

    def same_index_checker(entity_index, range):
        for item in entity_index:
            if item in range:
                return item
        return None

    def result_entity(food_index, capacity_index, quantity_index, tare_dict, tokens):
        result_return = str()
        result_dict = dict()
        tare_index = list(tare_dict.keys())

        for food in food_index:
            if food_index.index(food) == 0:
                food_range = range(0, food + 1)
            else:
                food_range = range(food_index[(food_index.index(food) - 1)], food + 1)

            quantity_cheker = same_index_checker(quantity_index, food_range)
            capacity_cheker = same_index_checker(capacity_index, food_range)
            tare_cheker = same_index_checker(tare_index, food_range)

            if quantity_cheker is None and \
                    tare_cheker is None and \
                    capacity_cheker is not None:
                result_item = str(re.findall(r'\d+', tokens[capacity_cheker])[0])
                result = str(result_item + " gramme of " + str(tokens[food]) + '\n')
                result_return += result
                result_dict[str(tokens[food])] = list([str(result_item), "gramme"])
            elif quantity_cheker is None and \
                    tare_cheker is not None and \
                    capacity_cheker is None:
                result_item = tare_food_dict[tokens[tare_cheker]]
                result = str(str(result_item) + " gramme of " + str(tokens[food]) + '\n')
                result_return += result
                result_dict[str(tokens[food])] = list([str(result_item), "gramme"])
            elif quantity_cheker is not None and \
                    tare_cheker is None and \
                    capacity_cheker is None:
                result_item = str(re.findall(r'\d+', tokens[quantity_cheker])[0])
                result = str(result_item + " units of " + str(tokens[food]) + '\n')
                result_return += result
                result_dict[str(tokens[food])] = list([str(result_item), "units"])
            elif quantity_cheker is not None and \
                    tare_cheker is not None and \
                    capacity_cheker is None:
                qua_item = int(tokens[quantity_cheker])
                tare_item = int(tare_food_dict[tokens[tare_cheker]])
                result_item = qua_item * tare_item
                result = str(str(result_item) + " gramme of " + str(tokens[food]) + '\n')
                result_return += result
                result_dict[str(tokens[food])] = list([str(result_item), "gramme"])
            '''elif quantity_cheker is None and \
                    tare_cheker is None and \
                    capacity_cheker is None:
                result = str("1 units of " + str(tokens[food]))
                print(result)'''
        return result_return, result_dict

    food_list = list()
    with open('food.csv') as csvfile:
        for row in csvfile:
            line = csvfile.readline()
            item = line.split(',')
            food_list.append(item[0][1:].lower())  # [1:] очистка от кавычек

    g_food_list = list()
    with open('generic-food.csv') as csvfile2:
        for row in csvfile2:
            line = csvfile2.readline()
            item = line.split(',')
            # print(item)
            g_food_list.append(item[0].lower())

    v_f_food_list = list()
    with open('v_f_food.csv') as csvfile3:
        for row in csvfile3:
            v_f_food_list.append(str(row)[:-1].lower())

    all_food_list = food_list + g_food_list + v_f_food_list
    # print(all_food_list)

    tare_food_dict = dict()
    columns = ['tare', 'capacity']
    data = pd.read_csv('food_tare.csv', delimiter=',', names=columns)
    for index, row in data.iterrows():
        tare_food_dict[row.tare] = row.capacity

    translator = Translator()
    nlp = spacy.load('food_ner')

    # columns = ['Raw_text', 'english', 'coma_separate', 'food_entity']
    # data = pd.read_csv('food_test.csv', delimiter='\n', names=columns)
    columns = ['Raw_text', 'Time_stamp', 'english', 'coma_separate', 'food_entity']
    data = pd.read_csv('food_test.csv', delimiter=',', names=columns, doublequote=False)

    columns2 = ['Time_stamp', 'Client', 'Value', 'Dimension', 'Food']
    data_food = pd.DataFrame(columns=columns2)
    # dict_result_index = int(0)

    display(HTML('<br>'))
    display(HTML('<font size="6">Example of highlighting previously described search objects</font>'))
    display(HTML('<br>'))
    for index, row in data.iterrows():
        row_food = str()
        english_str = translator.translate(row.Raw_text, dest='en').text
        data['english'][index] = english_str
        data['coma_separate'][index] = english_str.split(',')
        for coma_lines in data.coma_separate[index]:
            line_tokens = list()
            line_tokens_raw = nltk.word_tokenize(coma_lines)
            for token in line_tokens_raw:
                try:
                    clear_token = w2n.word_to_num(token)
                    line_tokens.append(str(clear_token))
                except ValueError:
                    line_tokens.append(token)

            food_list = food_entity_detect(line_tokens, all_food_list)
            capacity_list = capacity_detect(line_tokens)
            quantity_list = quantity_detect(line_tokens, capacity_list)
            tare_dict = tare_detect(line_tokens, tare_food_dict)

            line_result, dict_result = result_entity(food_list,
                                                     capacity_list,
                                                     quantity_list,
                                                     tare_dict,
                                                     line_tokens)
            row_food += line_result

            for food in dict_result.keys():
                client = 'Client name or id'
                row = list([data['Time_stamp'][index], client, dict_result[food][0], dict_result[food][1], food])
                data_food.loc[len(data_food)] = row
                '''data_food['Client'][dict_result_index] = 'Client name or id'
                data_food['Time_stamp'][dict_result_index] = data['Time_stamp'][index]
                data_food['Value'][dict_result_index] = dict_result[food][0]
                data_food['Dimension'][dict_result_index] = dict_result[food][1]
                data_food['Food'][dict_result_index] = food
                dict_result_index += 1'''

        data['food_entity'][index] = row_food

        doc = nlp(english_str)
        displacy.render(doc, style='ent', jupyter=True, options=options)

    data_food['Time_stamp'] = pd.to_datetime(data_food["Time_stamp"], unit='s')
    data_food = data_food.sort_values(by='Time_stamp')
    # data_food = data_food[['Time_stamp', 'Client', 'Value', 'Dimension' 'Food']]
    data.drop(['coma_separate', 'Time_stamp'], axis=1, inplace=True)
    # data.style.set_properties(**{'font-size':'20pt'})
    display(HTML('<br>'))
    display(HTML('<font size="6">Algorithm results table</font>'))
    display(HTML('<br>'))
    display(HTML(data.to_html().replace("\\n", "<br>")))
    display(HTML('<br>'))
    display(HTML('<font size="6">Example of storage and results presentation'
                 'to nutritioniststaking into account the customer\'s personification and meal history</font>'))
    display(HTML(data_food.to_html(index=False)))

