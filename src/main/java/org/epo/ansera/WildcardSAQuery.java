package org.epo.ansera;

import org.apache.lucene.index.FilteredTermsEnum;
import org.apache.lucene.index.Term;
import org.apache.lucene.index.Terms;
import org.apache.lucene.index.TermsEnum;
import org.apache.lucene.search.MultiTermQuery;
import org.apache.lucene.util.AttributeSource;
import org.apache.lucene.util.BytesRef;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.lang.Override;
import java.lang.String;
import java.util.Arrays;

public class WildcardSAQuery extends MultiTermQuery {

    /**
     * Will be better to use this one, but for debug purposes, I use org.epo.ansera.WildcardSAQuery#DELIMETER
     */
    public static final char NULL_DELIMETER = '\u0000';
    public static final char DELIMETER = '#';

    private final Term term;
    private final byte[] text;
    private final int[] sa;

    public WildcardSAQuery(String field, Term term) throws IOException {
        super(field);
        SuffixArrayMap.readSA(field);
        sa = SuffixArrayMap.getSAByFieldName(term.field());
        text = SuffixArrayMap.getTextByFieldName(term.field());
//        todo possible place for improvements
        this.term = term;
    }

    @Override
    protected TermsEnum getTermsEnum(Terms terms, AttributeSource atts) throws IOException {
        return new WildcardSATermEnum(terms.iterator(null));
    }

    @Override
    public String toString(String field) {
        return "WildcardSA ( " + term.field() + " : " + term.text() + " )";
    }

    private class WildcardSATermEnum extends FilteredTermsEnum {

        private final int end;
        private int index;
        //        private final PrintWriter out;
        private final byte[] bytes;
        private final String pattern;

        public WildcardSATermEnum(TermsEnum tenum) throws FileNotFoundException {
            super(tenum);
//            out = new PrintWriter(new File("C://App/info.log"));
//            out.println("------start-----------");
            bytes = term.text().getBytes();
            pattern = term.text();
//            for (int i = 1; i < sa.length; i += 10000) {
//                out.println((char) text[sa[i]]);
//            }
//            long start = System.nanoTime();
            index = findStartPos(bytes);
            end = findEndPos(bytes);
//            out.println("index = " + index);
//            out.println("end = " + end);
//            out.println("finding boundaries takes = " + (System.nanoTime() - start) + " nano s");
//            out.println("----------------------");
//            out.flush();
//            out.close();
        }

        @Override
        public BytesRef next() throws IOException {
            while (index <= end) {
                return getSuffix();
            }
            return null;
        }

        private BytesRef getSuffix() {
            while (index <= end) {
                int positionInText = sa[index++];
                if (positionInText >= 0 && positionInText < text.length && text[positionInText] != DELIMETER) {
                    int i = positionInText;
                    while (i > 0 && i < text.length && text[i] != DELIMETER) {
                        i--;
                    }
                    int j = positionInText;
                    while (j >= 0 && j < text.length - 1 && text[j] != DELIMETER) {
                        j++;
                    }
                    final String substring = new String(Arrays.copyOfRange(text, i + 1, j));
                    // todo possible it shouldn't be like that
                    if (substring.contains(pattern)) {
                        return new BytesRef(text, i + 1, j - i - 1);
                    }
                }
            }
            return null;
        }

        private int findEndPos(byte[] search) {
            int left = 0;
            int right = sa.length - 1;
            int mid;
            while (left < right) {
                mid = (left + right) / 2;
                int posInText = sa[mid];
                int i = 0, j = posInText;
                for (; j < text.length && i < search.length && text[j] == search[i] && text[j] != DELIMETER; ++i, ++j)
                    ;
                if (i == search.length) {
                    left = mid + 1;
                } else if (search[i] > text[j]) {
                    left = mid + 1;
                } else {
                    right = mid - 1;
                }
            }
            return (left + right) / 2;
        }

        private int findStartPos(byte[] search) {
            int left = 0;
            int right = sa.length - 1;
            int mid;
            while (left < right) {
                mid = (left + right) / 2;
                int posInText = sa[mid];
                int i = 0, j = posInText;
                for (; j < text.length && i < search.length && text[j] == search[i] && text[j] != DELIMETER; ++i, ++j)
                    ;
                if (i == search.length) {
                    right = mid - 1;
                } else if (search[i] > text[j]) {
                    left = mid + 1;
                } else {
                    right = mid - 1;
                }
            }
            return (left + right) / 2;
        }

        @Override
        protected AcceptStatus accept(BytesRef term) throws IOException {
            return null;
        }
    }
}
