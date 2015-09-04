# purepos-python3
PurePOS reimplemented in Python3.

Version: [2.4.90 (beta)](RELEASENOTES.md)

Released: 2015.09.04.

PurePos
=======
PurePos is an open-source HMM-based automatic morphological annotation tool.
It can perform tagging and lemmatization at the same time, it is very fast to train, with the
possibility of easy integration of symbolic rule-based components into the annotation process
that can be used to boost the accuracy of the tool.
The hybrid approach implemented in PurePos is especially beneficial in the case of rich morphology,
highly detailed annotation schemes and if a small amount of training data is available.

***Differences to PurePOS 2.1***
* The word-lemma-tag separator character (traditionally #) can be specified both for training and
tagging
* The path of morphological analyser module (*Humor*) and also the path of *lex* files can be
specified
* The standard output tagging can be colored for easier reading
* Special characters bug fixed (at  the four-bytes unicode chars)
* LemmaTransformation at hyphened lemma bug fixed
* Smaller model files
* The old binary models are no more compatibily with the new version

For more see the [Release notes](RELEASENOTES.md) and the [Issue tracker](https://github.com/ppke-nlpg/purepos-python3/issues/).

Usage
---------
***Dependencies***
* Python >=3.4

***Trainig*** the tagger needs a corpus with  the following format:
* Sentences are separated in new lines, while there are spaces between tagged words
* Each token in a sentence must be annotated with its lemma and POS tag separated by a given
separator (default: hashmark): `word#lemma#tag`

`$ python3 purepos.py train -m model_file.dat -i tagged_input.txt [-S "#"]`

***Tagging*** raw text from file or std input which is to be tagged must contain:
* Sentences in new lines
* Words separated by spaces (also punct-type chars)

`$ python3 purepos.py tag -m model_file.dat [-S "#"] [-i raw_input.txt] [-o tagged_output.txt]`

***Other optional arguments:***

    -h, --help          show this help message and exit
    -m <modelfile>, --model <modelfile>
                        Specifies a path to a model file. If an exisiting
                        model is given for training, the tool performs
                        incremental training.
    -t <number>, --tag-order <number>
                        Order of tag transition. Second order means trigram
                        tagging. The default is 2. Training only option.
    -e <number>, --emission-order <number>
                        Order of emission. First order means that the given
                        word depends only on its tag. The default is 2.
                        Training only option.
    -s <length>, --suffix-length <length>
                        Use a suffix trie for guessing unknown words tags with
                        the given maximum suffix length. The default is 10.
                        Training only option.
    -r <treshold>, --rare-frequency <treshold>
                        Add only words to the suffix trie with frequency less
                        than the given treshold. The default is 10. Training
                        only option.
    -a <analyzer>, --analyzer <analyzer>
                        Set the morphological analyzer. <analyzer> can be
                        'none', 'integrated' or a file :
                        <morphologicalTableFile>. The default is to use the
                        integrated one. Tagging only option.
    -H <path>, --pyhumor-path <path>
                        Set the path of the PyHumor module where the Humor
                        class is defined.
    -L <path>, --lex-path <path>
                        Set the path of the lex file used by the Humor
                        analyser. The pyhumor module delivered lex is used.
    --only-pos-tags     Do not perform stemming, output only POS tags. Tagging
                        only option.
    -g <number>, --max-guessed <number>
                        Limit the max guessed tags for each token. The default
                        is 10. Tagging only option.
    -n <number>, --max-results <number>
                        Set the expected maximum number of tag sequences (with
                        its score). The default is 1. Tagging only option.
    -b <theta>, --beam-theta <theta>
                        Set the beam-search limit. The default is 1000.
                        Tagging only option.
    -o <file>, --output-file <file>
                        File where the tagging output is redirected. Tagging
                        only option.
    --color-stdout      Use colored console if the stdout is the choosen
                        output.
    -c <encoding>, --encoding <encoding>
                        Encoding used to read the training set, or write the
                        results. The default is your OS default.
    --input-separator <separators>
                        Separator characters and tag starting character for
                        annotated input (divided by the first character cf.
                        sed). Eg.: "#{{#||#}}#["
    -S <separator>, --separator <separator>
                        Separator character between word, lemma and tags.
                        Default: '#'
    -i <file>, --input-file <file>
                        File containg the training set (for tagging) or the
                        text to be tagged (for tagging). The default is the
                        standard input.
    -d, --beam-decoder  Use Beam Search decoder. The default is to employ the
                        Viterbi algorithm. Tagging only option.
    -f <file>, --config-file <file>
                        Configuratoin file containg tag mappings. Defaults to
                        do not map any tag.
API
---
The PurePos is able to be loaded as a Python module. The basic usage is pretty simple:
```python
    from purepos import PurePos

    PurePos.train(*args)
    PurePos.tag(*args)
```
For more about the args read the [complete reference](REFERENCE.md).

References
----------

If you use the tool, please cite the following papers:
* [**PurePos 2.0: a hybrid tool for morphological disambiguation.** Orosz, G.; and Novák, A. *In Proceedings of the International Conference on Recent Advances in Natural Language Processing (RANLP 2013)*, page 539–545, Hissar, Bulgaria, 2013. INCOMA Ltd. Shoumen, BULGARIA.](http://aclweb.org/anthology//R/R13/R13-1071.pdf)
* [**PurePos – an open source morphological disambiguator.** Orosz, G.; and Novák, A. In Sharp, B.; and Zock, M., editor, *In Proceedings of the 9th International Workshop on Natural Language Processing and Cognitive Science*, page 53–63, Wroclaw, 2012. ](https://github.com/downloads/ppke-nlpg/purepos/purepos.pdf)
