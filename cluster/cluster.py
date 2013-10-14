# -*- coding: cp1252 -*-

'''
A generalized version of the precision recall module.
Is based on the precisionRecallSlice/precisionRecallSuffix modules
authored by Richard Moe.

@author: Snorre Magnus Dav�en, Richard Elling Moe.

@version: 2012.12.14
'''

from compactTrie.clustersPlus import *
from text.suffixTrees import suffixTree
from text.sliceTrees import midSliceTree, rangeSliceTree, n_slice_tree
from text.phrases import stringToPhrase
from time import time
from datetime import datetime
# from wordOccurrence import *


## Define module constants ....

## Tree types
SUFFIXTREE = 0
MIDSLICE = 1
RANGESLICE = 2
NSLICE = 3

## Verbosity
NONVERBOSE = 0
VERBOSE = 1
VERBOSEFILE = 2


def calcPrecisionRecallFMeasure(chromosome, clusterSettings):
    '''Returns the result of clustering the snippet collection given a set of 
    parameters.

    The calcPrecisionRecallFMeasure method takes a set of parameters pertaining
    to the compact trie clustering algorithm and clusters a snippet collection
    given these parameters. The results, precision, recall, F-Measure and tag
    accuracy, are calculated given the resulting clusters and a ground truth 
    definition.

    Args:
        chromosome (Chromosome): a chromosome representing the parameter list
        clusterSettings (ClusterSettings): an object wrapping info and settings:
            shouldDropSingletonGroundTruthClusters (int): boolean (0,1)
            tagindex (dict): an index of tags {"source": "tags"} generated from the
                            snippet collection
            filename (string): the file to use for building the tree
            groundTruthClusters (dict): an index {tags: [source, ..]} of ground
                                    truth clusters
            fBetaConstant (float): the beta constant to be used in the Fb-Measure
                                score calculations
            verbose (int): boolean (0,1), if function should print results to
                        console/terminal

    Returns:
        a tuple consisting of five "sub"-tuples
            1. (timeTocluster, noOfCluster, noOfBaseClusters)
            2. (precision, recall, fMeasure)
            3. (groundTruth0, groundTruth1, ..., groundTruth5)
            4. (groundTruthRep0, groundTruthRep1, ..., groundTruthRep5)
            5. (fMeasure0, fMeasure1, ..., fMeasure5)
    '''

    shouldDropSingletonGroundTruthClusters = clusterSettings.dropSingletonGTClusters
    tagIndex = clusterSettings.tagIndex
    snippetCollection = clusterSettings.snippetCollection
    filename = clusterSettings.snippetFile
    groundTruthClusters = clusterSettings.groundTruthClusters
    fBetaConstant = clusterSettings.fBetaConstant
    verbose = clusterSettings.verbosity
    if(shouldDropSingletonGroundTruthClusters == 1):
        groundTruthClusters = dropSingletonGroundTruthClusters(groundTruthClusters)

    ## Keep track of time for timing purposes
    start = time()

    ## Make tree from suffixes, midslices, rangeslices or n-slices
    tree = generate_compact_trie(chromosome.treeType, snippetCollection)

    ## Extract base clusters from compact trie given
    ## stop word parameters and number of clusters...
    baseClusters = topBaseClusters(tree,
                                   chromosome.topBaseClustersAmount,
                                   chromosome.minTermOccurrenceInCollection,
                                   chromosome.maxTermRatioInCollection,
                                   chromosome.minLimitForBaseClusterScore,
                                   chromosome.maxLimitForBaseClusterScore)

    if(chromosome.shouldDropSingletonBaseClusters == 1):
        baseClusters = dropSingletonBaseClusters(baseClusters)

    noOfBaseClusters = len(baseClusters)
    mergedComponents = None
    clusters = None
    if not noOfBaseClusters == 0:
        mergedComponents = mergeComponents(baseClusters)
        clusters = makeClusters(mergedComponents)
        if(chromosome.shouldDropOneWordClusters == 1):
            clusters = dropOneWordClusters(clusters)

    stop = time()
    timeToCluster = stop - start

    if noOfBaseClusters == 0:
        return ((timeToCluster, 0, noOfBaseClusters),
            (.0, .0, .0),
            (.0, .0, .0, .0, .0),
            (.0, .0, .0, .0, .0),
            (.0, .0, .0, .0, .0))

    noOfSources = len(tagIndex)
    noOfClusters = len(clusters)
    noOfGTClusters = len(groundTruthClusters)

    ## For hopeless cases where no clusters are found
    if noOfClusters == 0:
        return ((timeToCluster, 0, noOfBaseClusters),
            (.0, .0, .0),
            (.0, .0, .0, .0, .0),
            (.0, .0, .0, .0, .0),
            (.0, .0, .0, .0, .0))

    resultsTagAccuracy = calc_tag_accuracy(clusters,
                                           noOfClusters,
                                           groundTruthClusters,
                                           tagIndex)

    resultsGroundTruth = calc_ground_truth(clusters,
                                           noOfClusters,
                                           groundTruthClusters,
                                           tagIndex)

    resultsGroundTruthRep = calc_gt_represented(clusters,
                                                          noOfClusters,
                                                          groundTruthClusters,
                                                          tagIndex)

    resultsFMeasure = calc_f_measure(resultsGroundTruth,
                                     resultsGroundTruthRep,
                                     fBetaConstant)

    precision = calc_overall_precision(groundTruthClusters,
                                       clusters,
                                       noOfSources)

    recall = calc_overall_recall(groundTruthClusters,
                                 clusters,
                                 noOfSources)

    fMeasure = calc_overall_fmeasure(groundTruthClusters,
                                     clusters,
                                     noOfSources,
                                     fBetaConstant)

    optionsString = make_options_string(chromosome.treeType,
                                        chromosome.topBaseClustersAmount,
                                        chromosome.minTermOccurrenceInCollection,
                                        chromosome.maxTermRatioInCollection,
                                        shouldDropSingletonGroundTruthClusters,
                                        chromosome.shouldDropSingletonBaseClusters,
                                        chromosome.shouldDropOneWordClusters,
                                        tagIndex,
                                        snippetCollection,
                                        filename,
                                        groundTruthClusters,
                                        fBetaConstant,
                                        verbose,
                                        timeToCluster)

    resultsString = make_precision_recall_fMeasure_string(precision,
                                                          recall,
                                                          fMeasure,
                                                          fBetaConstant)

    detailedResultsString = make_results_string(resultsTagAccuracy,
                                                resultsGroundTruth,
                                                resultsGroundTruthRep,
                                                noOfClusters,
                                                noOfGTClusters)
    if verbose == VERBOSE:
        print(optionsString)
        print(resultsString)
        print(detailedResultsString)
    elif verbose == VERBOSEFILE:
        writeResultsToFile(optionsString,
                           resultsString,
                           detailedResultsString)

    # Get the two best ground truth and recall value overlap values from result
    groundTruthTuple = getOverlapResultTuple(resultsGroundTruth, 2)
    groundTruthRepTuple = getOverlapResultTuple(resultsGroundTruthRep, 2)
    fMeasureTuple = getOverlapResultTuple(resultsFMeasure, 1)

    return ((timeToCluster, noOfClusters, noOfBaseClusters),
            (precision, recall, fMeasure),
            groundTruthTuple,
            groundTruthRepTuple,
            fMeasureTuple)


def getOverlapResultTuple(resultsGroundTruth, position):
    resultTuple = ()
    for resultsOverlapX in resultsGroundTruth:
        # Get the fraction of clusters to the total amount...
        resultTuple += (resultsOverlapX[position],)
    return resultTuple


def make_options_string(treeType,
                               topBaseClustersAmount,
                               minTermOccurrenceInCollection,
                               maxTermRatioInCollection,
                               shouldDropSingletonGroundTruthClusters,
                               shouldDropSingletonBaseClusters,
                               shouldDropOneWordClusters,
                               tagIndex,
                               snippetCollection,
                               filename,
                               groundTruthClusters,
                               fBetaConstant,
                               verbosity,
                               time):
    '''Generates a string listing clustering algorithm options

    Returns:
        A string containing the options
    '''
    optionsString = ""
    optionsString += "######################################################\n"
    optionsString += "Clustered snippet collection of file: " + filename + \
                    " in %.4f" % (time) + " seconds\n"
    optionsString += make_tree_type_text(treeType)
    optionsString += "Number of top base clusters: " + \
                    str(topBaseClustersAmount) + "\n"
    optionsString += "Minimum term/word occurrence in collection: " + \
                    str(minTermOccurrenceInCollection) + "\n"
    optionsString += "Maximum term/word occurrence ratio in collection: " + \
                    str(maxTermRatioInCollection) + "\n"
    if shouldDropSingletonGroundTruthClusters:
        optionsString += "Singleton ground truth clusters excluded\n"
    else:
        optionsString += "Singleton ground truth clusters included\n"
    if shouldDropSingletonBaseClusters:
        optionsString += "Singleton base clusters excluded\n"
    else:
        optionsString += "Singleton base clusters excluded\n"
    if shouldDropOneWordClusters:
        optionsString += "One word clusters excluded\n"
    else:
        optionsString += "One word clusters included\n"
    optionsString += "F-beta constant used for F-Measure: " + \
                    str(fBetaConstant) + "\n"
    optionsString += "---------------------\n"
    return optionsString


def make_precision_recall_fMeasure_string(precision,
                                          recall,
                                          fMeasure,
                                          fBetaConstant):
    resultString = "The overall measurements of clusters:\n"
    resultString += "Precision:\t\t" + "%.3f" % (precision) + "\n"
    resultString += "Recall:\t\t\t" + "%.3f" % (recall) + "\n"
    resultString += "F-Measure (b=%.1f" % (fBetaConstant) + "):\t" \
        + "%.3f" % (fMeasure) + "\n\n"
    return resultString


def make_results_string(resultsTagAccuracy,
                        resultsGroundTruth,
                        resultsGroundTruthRep,
                        noOfClusters,
                        noOfGTClusters):
    tagAccuracy = "Tag Accuracy:\n"
    tagAccuracy += "Overlap - Number/NoClusters - Fraction - Accumulated\n"
    tagAccuracy += "----------------------------------------------------\n"
    for (i, countMatch, fraction, accumulated) in resultsTagAccuracy:
        tagAccuracy += str(i) + "\t   %2i" % (countMatch) + "/" + \
                            str(noOfClusters) + \
                            "\t\t%.3f" % (fraction) + "\t   " + \
                            "%.3f" % (accumulated) + "\n"

    groundTruthString = "Ground truth:\n"
    groundTruthString += "Overlap - Number/NoClusters - Fraction - Accumulated\n"
    groundTruthString += "----------------------------------------------------\n"
    for (i, countMatch, fraction, accumulated) in resultsGroundTruth:
        groundTruthString += str(i) + "\t   %2i" % (countMatch) + "/" + \
                            str(noOfClusters) + \
                            "\t\t%.3f" % (fraction) + "\t   " + \
                            "%.3f" % (accumulated) + "\n"

    groundTruthRepString = "Ground truth represented:\n"
    groundTruthRepString += "Overlap - Number/NoClusters - Fraction - Accumulated\n"
    groundTruthRepString += "----------------------------------------------------\n"
    for (i, countMatch, fraction, accumulated) in resultsGroundTruthRep:
        groundTruthRepString += str(i) + "\t   %2i" % (countMatch) + "/" + \
                                str(noOfGTClusters) + \
                                "\t\t%.3f" % (fraction) + "\t   " + \
                                "%.3f" % (accumulated) + "\n"

    return tagAccuracy + "\n" + groundTruthString + "\n" + groundTruthRepString


def make_tree_type_text(treeTypeTuple):
    (treeType, sliceLengthRangeMin, rangeMax) = treeTypeTuple
    text = 'Tree type: '
    if treeType == SUFFIXTREE:
        text += 'Suffix'
    elif treeType == MIDSLICE:
        text += 'mid slice'
    elif treeType == RANGESLICE:
        text += 'range slice with min ' + str(sliceLengthRangeMin) + \
                ' & max ' + str(rangeMax)
    else:
        text += 'n slice of length '
        text += str(sliceLengthRangeMin)
    return text


def writeResultsToFile(optionsString,
                       resultsString,
                       detailedResultsString):
    filename = str(datetime.now())
    detailedResults = open("../" + filename + ".txt", "w")
    detailedResults.write(optionsString)
    detailedResults.write(resultsString)
    detailedResults.write(detailedResultsString)
    detailedResults.close()


def generate_compact_trie(treeTypeTuple, snippetCollection):
    (treeType, sliceLengthRangeMin, rangeMax) = treeTypeTuple
    if treeType == SUFFIXTREE:
        return suffixTree(snippetCollection)
    elif treeType == MIDSLICE:
        return midSliceTree(snippetCollection)
    elif treeType == RANGESLICE:
        return rangeSliceTree(snippetCollection, sliceLengthRangeMin, rangeMax)
    elif treeType == NSLICE:
        return n_slice_tree(sliceLengthRangeMin, snippetCollection)


def calc_tag_accuracy(clusters,
                      noOfClusters,
                      groundTruthClusters,
                      tagindex):

    def count_match(discrepancy):
        count = 0
        for cluster in clusters:
            tagList = []
            for source in cluster.sources:
                string = tagindex[source].replace('-', ' ')
                tagList.append(stringToPhrase(string))
            if len(common(map(lambda cluster:
                              cluster, tagList))) == 5 - discrepancy:
                count += 1
        return count

    ## Make a list of tuples containing count match results
    matchResult = []
    for i in range(6):
        countMatch = count_match(i)
        p = 0
        for k in range(i):
            p += count_match(k)
        ## Tuple (index, countMatch, ratio, accumulated)
        matchResult.append((i,
                            countMatch,
                            countMatch / float(noOfClusters),
                            (p + countMatch) / float(noOfClusters)))
    return matchResult


def calc_ground_truth(clusters,
                      noOfClusters,
                      groundTruthClusters,
                      tagindex):
    count = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for cluster in clusters:
        bestMatch = 0
        for gtcKey in groundTruthClusters.keys():
            if contains(cluster.sources, groundTruthClusters[gtcKey]):
                ## Make a list of tags occurring in the cluster's sources
                tagList = []
                for source in cluster.sources:
                    string = tagindex[source].replace('-', ' ')
                    tagList.append(stringToPhrase(string))
                gtcKeyString = gtcKey.replace('-', ' ')
                tagList.append(stringToPhrase(gtcKeyString))
                d = len(common(map(lambda cluster: cluster, tagList)))
                if d > bestMatch:
                    bestMatch = d
        count[bestMatch] += 1

    groundTruthResults = []
    for i in (5, 4, 3, 2, 1, 0):
        p = 0
        for k in range(i, 6):
            p += count[k]
        groundTruthResults.append((5 - i,
                                   count[i],
                                   count[i] / float(noOfClusters),
                                   p / float(noOfClusters)))
    return groundTruthResults


def calc_gt_represented(clusters,
                                  noOfClusters,
                                  groundTruthClusters,
                                  tagindex):
    count = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for gtcKey in groundTruthClusters.keys():
        bestMatch = 0
        for cluster in clusters:
            if contains(cluster.sources, groundTruthClusters[gtcKey]):
                tagList = []
                for source in cluster.sources:
                    string = tagindex[source].replace('-', ' ')
                    tagList.append(stringToPhrase(string))
                gtcKeyString = gtcKey.replace('-', ' ')
                tagList.append(stringToPhrase(gtcKeyString))
                d = len(common(map(lambda(cluster):
                                   cluster, tagList)))
                if d > bestMatch:
                    bestMatch = d
        count[bestMatch] += 1

    result = []
    for i in (5, 4, 3, 2, 1, 0):
        p = 0
        for k in range(i, 6):
            p = p + count[k]
        result.append((5 - i,
                       count[i],
                       count[i] / float(len(groundTruthClusters)),
                       p / float(len(groundTruthClusters))))
    return result


def calc_f_measure(groundTruth, groundTruthRep, fBetaConstant):
    fMeasureResults = []
    for i in range(len(groundTruth)):
        precision = groundTruth[i][2]  # Get precision fraction
        recall = groundTruthRep[i][2]  # Get recall fraction

        ## Calc F-measure as the weighted average of precision and recall
        fMeasure = float(0)
        if not (precision == 0 and recall == 0):  # Never divide by zero
            numerator = precision * recall
            denominator = (math.pow(fBetaConstant, 2) * precision) + recall
            fMeasure = (1 + math.pow(fBetaConstant, 2)) * (numerator / denominator)

        fMeasureResults.append((groundTruth[i][0], fMeasure))
    return fMeasureResults

def calc_overall_precision(groundTruthClusters, clusters, noOfSources):
    '''Calculate precision of clusters given ground truth clusters

    This method implements an overall precision measurement based on the
    formula for the overall F-Measure described in the article:
    http://dx.doi.org/10.1145/1242572.1242590

    Args:
        groundtruthClusters (dict): a dictionary mapping tags to
                                    source list
        clusters (list): a list of cluster objects
        noOfSources (int): the number of sources in the collection

    Returns:
        The precision of the cluster result
    '''
    overallPrecision = 0.0
    ## For each category (gtctags) in groundTruthClusters
    for groundTruthTags in groundTruthClusters.keys():
        sources = groundTruthClusters.get(groundTruthTags)
        ## Find factor of category sources length to document number
        categoryFactor = float(len(sources)) / float(noOfSources)
        maxPrecision = 0.0
        ## Find max precision out of all clusters j given category i
        for cluster in clusters:
            intersectionLength = float(len(set(sources) & 
                                           set(cluster.sources)))
            precision = intersectionLength / float(len(cluster.sources))
            if precision > maxPrecision:
                maxPrecision = precision
        overallPrecision += categoryFactor * maxPrecision
    return overallPrecision


def calc_overall_recall(groundTruthClusters, clusters, noOfSources):
    '''Calculate recall of clusters given ground truth clusters

    This method implements an overall recall measurement based on the
    formula for the overall F-Measure described in the article:
    http://dx.doi.org/10.1145/1242572.1242590

    Args:
        groundtruthClusters (dict): a dictionary mapping tags to
                                    source list
        clusters (list): a list of cluster objects
        noOfSources (int): the number of sources in the collection

    Returns:
        The recall of the cluster result
    '''
    overallRecall = 0.0
    ## For each category (gtctags) in groundTruthClusters
    for groundTruthTags in groundTruthClusters.keys():
        sources = groundTruthClusters.get(groundTruthTags)
        ## Find factor of category sources length to document number
        categoryFactor = float(len(sources)) / float(noOfSources)
        maxRecall = 0.0
        ## Find max precision out of all clusters j given category i
        for cluster in clusters:
            intersectionLength = float(len(set(sources) & 
                                           set(cluster.sources)))
            recall = intersectionLength / float(len(sources))
            if recall > maxRecall:
                maxRecall = recall
        overallRecall += categoryFactor * maxRecall
    return overallRecall


def calc_overall_fmeasure(groundTruthClusters,
                          clusters,
                          noOfSources,
                          fBetaConstant):
    '''Calculate F-measure of clusters given ground truth clusters

    This method implements the formula for the overall F-Measure
    described in the article: http://dx.doi.org/10.1145/1242572.1242590

    Args:
        groundtruthClusters (dict): a dictionary mapping tags to
                                    source list
        clusters (list): a list of cluster objects
        noOfSources (int): the number of sources in the collection

    Returns:
        The recall of the cluster result
    '''
    overallFMeasure = 0.0
    ## For each category (gtctags) in groundTruthClusters
    for groundTruthTags in groundTruthClusters.keys():
        sources = groundTruthClusters.get(groundTruthTags)
        ## Find factor of category sources length to document number
        categoryFactor = float(len(sources)) / float(noOfSources)
        maxFMeasure = 0.0
        ## Find max precision out of all clusters j given category i
        for cluster in clusters:
            intersectionLength = float(len(set(sources) & 
                                           set(cluster.sources)))
            precision = intersectionLength / float(len(cluster.sources))
            recall = intersectionLength / float(len(sources))
            fMeasure = 0.0
            fBetaConstant = math.pow(fBetaConstant, 2)
            fMeasureNum = (fBetaConstant + 1) * precision * recall
            fMeasureDen = (fBetaConstant * precision) + recall
            if not fMeasureDen == 0:
                fMeasure = fMeasureNum / fMeasureDen
            if fMeasure > maxFMeasure:
                maxFMeasure = fMeasure
        overallFMeasure += categoryFactor * maxFMeasure
    return overallFMeasure


def dropSingletonGroundTruthClusters(gtcIndex):
    '''Returns a new dictionary with all singleton-value
    key-value pairs removed.'''
    Index = {}
    for k in gtcIndex.keys():
        if len(gtcIndex[k]) > 1:
            Index[k] = gtcIndex[k]
    return Index


## auxiliaries
def contains(list1, list2):  ## list1 contains list2
    for x in list2:
        if x not in list1: return False
    return True


def equal(list1, list2):
    return contains(list1, list2) and contains(list2, list1)

