package org.epo.ansera;

import java.io.File;
import java.io.IOException;
import java.lang.String;
import java.lang.StringBuilder;
import java.lang.System;
import java.util.*;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;

public class SuffixArrayMap {

    private static final Map<String, String> pathToSaMap = new HashMap<>();
    private static final Map<String, String> pathToTermsMap = new HashMap<>();
    private static final Map<String, byte[]> textByFieldName = new HashMap<>();
    private static final Map<String, int[]> saByFieldName = new HashMap<>();

    public static boolean isConfigured(String fieldName) {
        return pathToSaMap.containsKey(fieldName) && pathToTermsMap.containsKey(fieldName);
    }

    public static void addPathForSA(String fieldName, String pathToSA) {
        pathToSaMap.put(fieldName, pathToSA);
    }

    public static void addPathForTerms(String fieldName, String pathToTerms) {
        pathToTermsMap.put(fieldName, pathToTerms);
    }

    public static void readSA(String fieldName) throws IOException {
        if (!pathToTermsMap.containsKey(fieldName)) {
            throw new IllegalArgumentException("Field " + fieldName + " isn't configured for SA creation");
        }
        if (!pathToSaMap.containsKey(fieldName)) {
            throw new IllegalArgumentException("Field " + fieldName + " isn't configured for SA creation");
        }
        String pathToTerms = pathToTermsMap.get(fieldName);
        String pathToSA = pathToSaMap.get(fieldName);
        if (!textByFieldName.containsKey(fieldName) && !saByFieldName.containsKey(fieldName)) {
            System.out.println("Starting to read Terms text file...");
            Scanner in = new Scanner(new File(pathToTerms));
            StringBuilder sb = new StringBuilder();
            while (in.hasNext()) {
                sb.append(in.nextLine());
            }
            byte[] bytes = sb.toString().getBytes();
            textByFieldName.put(fieldName, bytes);
            System.out.println("Terms size " + (1.0d * bytes.length * 1) / 1024 / 1024 + " Mb");
            in.close();
            System.out.println("Starting to read SA file...");
            in = new Scanner(new File(pathToSA));
            int[] sa = new int[bytes.length];
            for (int i = 0; i < sa.length; ++i) {
                sa[i] = in.nextInt();
            }
            in.close();
            System.out.println("SA size " + (1.0d * sa.length * 4) / 1024 / 1024 + " Mb");
            saByFieldName.put(fieldName, sa);
        }
    }

    public static int[] getSAByFieldName(String fieldName) {
        return saByFieldName.get(fieldName);
    }

    public static byte[] getTextByFieldName(String fieldName) {
        return textByFieldName.get(fieldName);
    }
}
