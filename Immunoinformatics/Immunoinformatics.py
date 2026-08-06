"""
Entry point for the Immunoinformatics plugin
"""

from HorusAPI import Plugin


def create_plugin():
    """
    Generates the Immunoinformatics plugin and returns the instance
    """
    # ========== Plugin Definition ========== #

    immunoPlugin = Plugin()

    from Pages.setup_predig import setup_predig_page

    immunoPlugin.addPage(setup_predig_page)

    # ========== Blocks ========== #
    from Blocks.PredIG import predigBlock  # type: ignore

    immunoPlugin.addBlock(predigBlock)

    from Blocks.PredIGYamlInput import predigYamlInputBlock  # type: ignore

    immunoPlugin.addBlock(predigYamlInputBlock)

    # from Blocks.NOAH import noahBlock  # type: ignore

    # immunoPlugin.addBlock(noahBlock)

    # from Blocks.NetCleave import netCleaveBlock  # type: ignore

    # immunoPlugin.addBlock(netCleaveBlock)

    # from Blocks.PredIGmodels import predig_modelsBlock  # type: ignore

    # immunoPlugin.addBlock(predig_modelsBlock)

    # from Blocks.Tap import tapBlock  # type: ignore

    # immunoPlugin.addBlock(tapBlock)

    # ========== TCoaRse Blocks ========== #
    # Horus port of the tcoarse_prediction.nf Nextflow pipeline
    from Blocks.TCoaRse.AF3Outputs import af3OutputsBlock  # type: ignore
    from Blocks.TCoaRse.ContactMaps import contactMapsBlock  # type: ignore
    from Blocks.TCoaRse.CopyModels import copyModelsBlock  # type: ignore
    from Blocks.TCoaRse.Embeddings import embeddingsBlock  # type: ignore
    from Blocks.TCoaRse.EnergeticScorer import energeticScorerBlock  # type: ignore
    from Blocks.TCoaRse.MergeEnergies import mergeEnergiesBlock  # type: ignore
    from Blocks.TCoaRse.PairwiseDockQ import pairwiseDockQBlock  # type: ignore
    from Blocks.TCoaRse.PredictorBimodal import predictorBimodalBlock  # type: ignore
    from Blocks.TCoaRse.PredictorESMC import predictorESMCBlock  # type: ignore
    from Blocks.TCoaRse.PredictorTCoaRse import predictorTCoaRseBlock  # type: ignore
    from Blocks.TCoaRse.PyDockEnergies import pydockEnergiesBlock  # type: ignore
    from Blocks.TCoaRse.QualityMetrics import qualityMetricsBlock  # type: ignore
    from Blocks.TCoaRse.QualityTier import qualityTierBlock  # type: ignore
    from Blocks.TCoaRse.Similarities import similaritiesBlock  # type: ignore
    from Blocks.TCoaRse.StructureMetadata import structureMetadataBlock  # type: ignore

    for tcoarseBlock in [
        af3OutputsBlock,
        qualityMetricsBlock,
        qualityTierBlock,
        copyModelsBlock,
        structureMetadataBlock,
        similaritiesBlock,
        embeddingsBlock,
        predictorESMCBlock,
        pydockEnergiesBlock,
        contactMapsBlock,
        pairwiseDockQBlock,
        energeticScorerBlock,
        mergeEnergiesBlock,
        predictorTCoaRseBlock,
        predictorBimodalBlock,
    ]:
        immunoPlugin.addBlock(tcoarseBlock)

    # ========== Configs ========== #
    from Configs.columns_to_delete import columns_to_delete_config

    immunoPlugin.addConfig(columns_to_delete_config)

    from Configs.noah_model import noah_model

    immunoPlugin.addConfig(noah_model)

    from Configs.rscript import rscript_config

    immunoPlugin.addConfig(rscript_config)

    from Configs.python_exec import python_exec_config

    immunoPlugin.addConfig(python_exec_config)

    from Configs.noahConfig import noahExecutableConfig

    immunoPlugin.addConfig(noahExecutableConfig)

    from Configs.netCleaveConfig import netClaveExecutableConfig

    immunoPlugin.addConfig(netClaveExecutableConfig)

    from Configs.pchConfig import pchExecutableConfig

    immunoPlugin.addConfig(pchExecutableConfig)

    from Configs.mhcflurryConfig import mhcflurryExecutableConfig

    immunoPlugin.addConfig(mhcflurryExecutableConfig)

    from Configs.tapmapConfig import tapmatExecutableConfig

    immunoPlugin.addConfig(tapmatExecutableConfig)

    from Configs.tapMatConfig import tapMatConfig

    immunoPlugin.addConfig(tapMatConfig)

    from Configs.predigModelsConfig import predigModelsConfig

    immunoPlugin.addConfig(predigModelsConfig)

    from Configs.tcoarseConfig import tcoarseConfig

    immunoPlugin.addConfig(tcoarseConfig)

    # ========== Pages ========== #

    from Pages.results import results_page

    immunoPlugin.addPage(results_page)

    # Return the plugin
    return immunoPlugin


plugin = create_plugin()

"""Dependencies:
    "scikit-learn",
    "pandas",
    "numpy",
    "matplotlib",
    "argparse",
    "pathlib",
    "keras",
    "tensorflow",
    "biopython",
    "pytz",
    "pip mhcflurry",
    "rpy2",
    "pyyaml"
"""
