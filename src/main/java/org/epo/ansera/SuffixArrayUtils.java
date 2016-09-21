package org.epo.ansera;

import org.apache.lucene.index.*;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.NIOFSDirectory;
import org.apache.lucene.util.BytesRef;
import sais.sais;

import java.io.*;

public class SuffixArrayUtils {

    /**
     * Generate suffix array, using sais library - https://sites.google.com/site/yuta256/sais
     * sais.java just copied to this project
     *
     * @param pathToTerms path to terms file (concatenation of all terms for some field)
     * @param pathToSA    path to SA output file
     * @throws IOException
     */
    public static void generateSA(String pathToTerms, String pathToSA) throws IOException {
        File output = new File(pathToSA);
        if (output.isFile()) {
            System.out.println("File already exists, no need to regenerate it");
            return;
        }
        long start = System.currentTimeMillis();
        System.out.print(pathToTerms + ": ");
        /* Open a file for reading. */
        File f = new File(pathToTerms);
        FileInputStream in = new FileInputStream(f);

        /* Allocate 5n bytes of memory. */
        byte[] T = new byte[(int) f.length()];
        in.read(T);
        int[] SA = new int[T.length];
        int n = SA.length;

        /* Construct the suffix array. */
        new sais().suffixsort(T, SA, n);

        PrintWriter out = new PrintWriter(output);
        for (int j = 0; j < SA.length; ++j) {
            out.println(SA[j]);
        }
        out.flush();
        out.close();
        System.out.println("SA generated. Takes " + (1.0d * System.currentTimeMillis() - start) / 1000 + " s");
    }

    /**
     * Generate concatenation of all terms for some field
     *
     * @param pathToIndex path to Lucene index
     * @param fieldName   fieldName, what should be used for concatenation
     * @param outputPath  path for terms concatenation file
     */
    public static void generateTerms(String pathToIndex, String fieldName, String outputPath) throws IOException {
        File f = new File(outputPath);
        if (f.isFile()) {
            System.out.println("File already exists, no need to regenerate it");
            return;
        }
        final Directory dir = new NIOFSDirectory(new File(pathToIndex));
        final IndexReader reader = DirectoryReader.open(dir);
        Terms terms = MultiFields.getTerms(reader, fieldName);
        TermsEnum termsEnum = terms.iterator(null);

        StringBuilder sb = new StringBuilder(WildcardSAQuery.DELIMETER);
        BytesRef next = termsEnum.next();
        while (next != null) {
            sb.append(next.utf8ToString()).append(WildcardSAQuery.DELIMETER);
            next = termsEnum.next();
        }
        FileOutputStream out = new FileOutputStream(f);
        out.write(sb.toString().getBytes());
        out.flush();
        out.close();
    }
}
