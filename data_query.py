def get_data_query(language_id=1):
    """
    Generates the SQL query to fetch data for the given language.

    Improvements over the original query:
    1. Uses LEFT JOIN for wordlists so untranslated symbols don't disappear from the document.
       It falls back to `readersdetail.english` if the translation is missing.
    2. Joins `sun.language` independently using a CROSS JOIN (or unconditional join)
       so language metadata is always present even if translations are missing.
    """

    return f"""
        SELECT
            readersdetail.readersdetailid,
            readersdetail.sectionid,
            readersdetail.unicodeid,
            readersdetail.pageorderby,

            readers.unicodeid AS sectionunicode,
            {"readers.sectionname" if language_id == 1 else "COALESCE(section_word.word, readers.sectionname)"} AS sectionname,
            readers.subsectionname AS subsectionname,
            readers.pdforderby,

            -- Fallback to the base English word if the target language translation is missing
            COALESCE(wordlists.word, readersdetail.english) AS word,

            readersdetail.unicodeid AS unicode_id_id,
            readersdetail.unicodeid || '.svg' AS svgname,

            wordlists.related_meaning,
            wordlists.made_from_word_1,
            wordlists.made_from_word_2,
            wordlists.made_from_word_3,

            language.txt_readers_dict_cover_1,
            language.txt_page_no

        FROM sun.readersdetail
        JOIN sun.readers
            ON readersdetail.sectionid = readers.sectionid
            AND readers.languageid = 1

        -- Get the language metadata completely independently of whether words are translated
        LEFT JOIN sun.language AS language
            ON language.language_id = {language_id}

        -- Left join the section title translation
        LEFT JOIN sun.wordlists AS section_word
            ON readers.unicodeid = section_word.unicode_id_id
            AND section_word.language_id_id = {language_id}

        -- Left join the actual symbol translation
        LEFT JOIN sun.wordlists AS wordlists
            ON readersdetail.unicodeid = wordlists.unicode_id_id
            AND wordlists.language_id_id = {language_id}

        ORDER BY readers.pdforderby, readersdetail.pageorderby ASC;
    """
