READERS_QUERY = """
        SELECT
            readersdetail.readersdetailid,
            readersdetail.sectionid,
            readersdetail.unicodeid,
            readersdetail.pageorderby,

            readers.unicodeid AS sectionunicode,
            readers.sectionname,
            readers.subsectionname,
            readers.pdforderby,

            wordlists.word,
            wordlists.unicode_id_id,
            wordlists.unicode_id_id || '.svg' AS svgname,
            wordlists.related_meaning,
            wordlists.made_from_word_1,
            wordlists.made_from_word_2,
            wordlists.made_from_word_3,
            wordlists.made_from_word_4,
            wordlists.made_from_word_5,
            wordlists.made_from_word_6,
            wordlists.made_from_word_7,

            language.txt_readers_dict_cover_1,
            language.txt_page_no

        FROM sun.readersdetail
        JOIN sun.readers
            ON readersdetail.sectionid = readers.sectionid
        JOIN sun.wordlists AS wordlists
            ON readersdetail.unicodeid = wordlists.unicode_id_id
           AND readers.languageid = wordlists.language_id_id
        JOIN sun.language AS language
            ON readers.languageid = language.language_id
        WHERE readers.languageid = %(language_id)s
        ORDER BY readers.pdforderby, readersdetail.pageorderby ASC;
        """
LANGUAGE_QUERY = """
    SELECT name, language_abvr
    FROM sun.language
    WHERE language_id = %(language_id)s
    """