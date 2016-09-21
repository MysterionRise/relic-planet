package org.epo.ansera;

import junit.framework.TestCase;
import org.apache.commons.lang3.RandomStringUtils;
import org.apache.commons.math3.stat.descriptive.rank.Median;
import org.apache.lucene.analysis.core.WhitespaceAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.IntField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.*;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.TopScoreDocCollector;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.MMapDirectory;
import org.apache.lucene.store.NIOFSDirectory;
import org.apache.lucene.util.Version;

import java.io.File;
import java.io.IOException;
import java.util.Random;

public class SABenchmark extends TestCase {

    /**
     * Test org.epo.ansera.WildcardSAQuery and provide some basic statistics (output into system)
     *
     * @param pathToIndex
     * @param numberOfIter  - number of iterations for test
     * @param fieldName     fieldName in query
     * @param searchPattern - should be similar to PQL syntax, +searchPattern+, e.g PQL - '+oo+' means 'oo' here
     */
    public static void testSAQuery(String pathToIndex, int numberOfIter, String fieldName, String searchPattern) throws IOException {
        if (!SuffixArrayMap.isConfigured(fieldName)) {
            SuffixArrayMap.readSA(fieldName);
        }
        final Directory dir = new MMapDirectory(new File(pathToIndex));
        IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_4_10_4, new WhitespaceAnalyzer());
        config.setMergePolicy(new LogDocMergePolicy());
        IndexWriter writer = new IndexWriter(dir, config);
        IndexReader reader = DirectoryReader.open(writer, true);
        System.out.println("Number of docs in index" + reader.numDocs());
        IndexSearcher searcher = new IndexSearcher(reader);
        double med[] = new double[numberOfIter];
        Median m = new Median();
        for (int i = 0; i < numberOfIter; ++i) {
            Query query = new WildcardSAQuery(fieldName, new Term(fieldName, searchPattern));
            TopScoreDocCollector collector = TopScoreDocCollector.create(10, true);
            long start = System.currentTimeMillis();
            searcher.search(query, collector);
            med[i] = System.currentTimeMillis() - start;
//            System.out.println("query: " + query);
//            System.out.println("memory: " + Runtime.getRuntime().totalMemory() / 1024 / 1024 + " Mb");
//            System.out.println("time: " + (1.0d * System.currentTimeMillis() - start) / 1000.0d + " seconds");
            System.out.println("numFound: " + collector.getTotalHits());
        }
        System.out.println("-----------report-------------------");
        System.out.println("med = " + m.evaluate(med));
        reader.close();
        writer.close();
    }

    /**
     * Shows the usage of these test methods
     *
     * @param args
     */
    public static void main(String[] args) throws IOException {
        String fieldName = "text";
        String pathToIndex = "C://App/fst_index";
        String pathToSA = "C://App/sa.txt";
        String pathToTerms = "C://App/terms.txt";
        generateIndex(pathToIndex);
        SuffixArrayUtils.generateTerms(pathToIndex, fieldName, pathToTerms);
        SuffixArrayUtils.generateSA(pathToTerms, pathToSA);
        SuffixArrayMap.addPathForSA(fieldName, pathToSA);
        SuffixArrayMap.addPathForTerms(fieldName, pathToTerms);
        testSAQuery(pathToIndex, 100, fieldName, "oo");
        // due to different reasons, this should be replaced with some dumb implementation from out of the box lucene
        testMagicQuery(pathToIndex, 100, fieldName, "oo");
    }

    private static void generateIndex(String pathToIndex) throws IOException {
        final Directory dir = new NIOFSDirectory(new File(pathToIndex));
        IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_4_10_4, new WhitespaceAnalyzer());
        config.setMergePolicy(new LogDocMergePolicy());
        IndexWriter writer = new IndexWriter(dir, config);
        for (int i = 0; i < 100_000; ++i) {
            if (i % 1_000 == 0) {
                writer.commit();
            }
            writer.addDocument(doc(i, generateTextWithNumbers()));
        }
        writer.commit();
        writer.close();
        dir.close();
    }


    private static String generateTextWithNumbers() {
        StringBuilder sb = new StringBuilder();
        Random r = new Random();
        for (int i = 0; i < 100; ++i) {
            if (r.nextInt(100) < 10) {
                sb.append(RandomStringUtils.randomNumeric(3)).append(" ");
            } else {
                sb.append(RandomStringUtils.randomAlphabetic(15)).append(" ");
            }
        }
        return sb.toString();
    }

    private static Document doc(int id, String text) {
        Document d = new Document();
        d.add(new IntField("id", id, Field.Store.YES));
        d.add(new TextField("text", text, Field.Store.YES));
        return d;
    }
}
