def get_data_query(language_id=1):
    """
    Generates the SQL query to fetch data for the given language.

    This query joins four key tables to assemble the report content:
    1. `readers` & `readersdetail`: Define the document structure (sections, subsections) and item ordering.
    2. `wordlists`: Provides the core dictionary content (words, made from words, and related meanings).
    3. `language`: Fetches the target language.

    It filters by the requested Language ID and pre-sorts the results by Section and Page Order.
    """

    return f"""
        SELECT
            readersdetail.readersdetailid,
            readersdetail.sectionid,
            readersdetail.unicodeid,
            readersdetail.pageorderby,

            readers.unicodeid AS sectionunicode,
            {"readers.sectionname" if language_id == 1 else "COALESCE(section_word.word, readers.sectionname)"} as sectionname,
            readers.subsectionname as subsectionname,
            readers.pdforderby,

            wordlists.word,
            wordlists.unicode_id_id,
            wordlists.unicode_id_id || '.svg' AS svgname,
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
        LEFT JOIN sun.wordlists AS section_word
            ON readers.unicodeid = section_word.unicode_id_id
            AND section_word.language_id_id = {language_id}
        JOIN sun.wordlists AS wordlists
            ON readersdetail.unicodeid = wordlists.unicode_id_id
        JOIN sun.language AS language
            ON wordlists.language_id_id = language.language_id
        WHERE wordlists.language_id_id = {language_id}
        ORDER BY readers.pdforderby, readersdetail.pageorderby ASC;
    """
