from __future__ import division
from __future__ import print_function
from past.utils import old_div
import sys
sys.path.insert(1,"../../../")
import h2o
from tests import pyunit_utils
from h2o.estimators.glm import H2OGeneralizedLinearEstimator
import pandas as pd
import numpy as np

# test missing_value handling for interactions.  This test is derived from Brian Scannell's code.  Thank you.
#  I have tested all three kinds of interactions with validation frame just to make sure my fix works properly.
def interactions():
    # test interaction of enum and enum columns
    print("Test interaction with enum by enum")
    pd_df_cat_cat_NA = pd.DataFrame(np.array([[1,0,1,0], ["a", "a", "b", "b"], ['Foo', 'UNKNOWN', 'Foo', 'Bar']]).T,
                                    columns=['label', 'categorical_feat', 'categorical_feat2'])
    pd_df_cat_cat = pd.DataFrame(np.array([[1,0,1,0], ["a", "a", "b", "b"], ['Foo', 'Foo', 'Foo', 'Bar']]).T,
                                 columns=['label', 'categorical_feat', 'categorical_feat2'])
    performOneTest(pd_df_cat_cat_NA, pd_df_cat_cat, interactionColumn= ['categorical_feat', 'categorical_feat2'],
                 xcols=['categorical_feat', 'categorical_feat2'])
 
    # # test interaction of enum and num columns
    print("Test interaction with enum by num")
    pd_df_cat_num_NA = pd.DataFrame(np.array([[1,0,1,0], [1,2,3,4], ['Foo', 'UNKNOWN', 'Foo', 'Bar']]).T,
                      columns=['label', 'numerical_feat', 'categorical_feat'])
    pd_df_cat_num = pd.DataFrame(np.array([[1,0,1,0], [1,2,3,4], ['Foo', 'Foo', 'Foo', 'Bar']]).T,
                                  columns=['label', 'numerical_feat', 'categorical_feat'])
    performOneTest(pd_df_cat_num_NA, pd_df_cat_num, interactionColumn= ['numerical_feat', 'categorical_feat'], 
                     xcols=['numerical_feat', 'categorical_feat'])
     
    # # test interaction of num and num columns
    print("Test interaction with num by num")
    pd_df_num_num_NA = pd.DataFrame(np.array([[1,0,1,0], [1,2,2,4], [2, 3, float('NaN'), 1]]).T,
                                columns=['label', 'numerical_feat', 'numerical_feat2'])
    pd_df_num_num = pd.DataFrame(np.array([[1,0,1,0], [1,2,2,4], [2, 3, 2, 1]]).T,
                                    columns=['label', 'numerical_feat', 'numerical_feat2'])
    performOneTest(pd_df_num_num_NA, pd_df_num_num, interactionColumn= ['numerical_feat', 'numerical_feat2'],
                   xcols=['numerical_feat', 'numerical_feat2'], standard=False)

def performOneTest(frameWithNA, frameWithoutNA, interactionColumn, xcols, standard=True):
    # default missing value handling = meanImputation
    h2o_df_NA = h2o.H2OFrame(frameWithNA, na_strings=["UNKNOWN"])
    h2o_df_NA_Valid = h2o.H2OFrame(frameWithNA, na_strings=["UNKNOWN"])
    h2o_df = h2o.H2OFrame(frameWithoutNA, na_strings=["UNKNOWN"])
    h2o_df_valid = h2o.H2OFrame(frameWithoutNA, na_strings=["UNKNOWN"])
    # build model with and without NA in Frame
    modelNA = H2OGeneralizedLinearEstimator(family = "Binomial", alpha=0, lambda_search=False,
                                            interactions=interactionColumn, standardize=standard)
    modelNA.train(x=xcols, y='label', training_frame=h2o_df_NA, validation_frame=h2o_df_NA_Valid)
    model = H2OGeneralizedLinearEstimator(family = "Binomial", alpha=0, lambda_search=False,
                                      interactions=interactionColumn, standardize=standard)
    model.train(x=xcols, y='label', training_frame=h2o_df, validation_frame=h2o_df_valid)
    # extract GLM coefficients
    coef_m_NA = modelNA._model_json['output']['coefficients_table']
    coef_m =  model._model_json['output']['coefficients_table']
    
    if not (len(coef_m_NA.cell_values)==len(coef_m.cell_values)):   # deal with 0 coeff for NA
        coef_m_NA_dict = coef_m_NA.cell_values
        coef_m = coef_m.cell_values
        coefNAIndex = 0
        for index in range(len(coef_m)):
            if not (coef_m_NA_dict[coefNAIndex][0]==coef_m[index][0]):  # skip over coefficients with NA that is 0.0
                coefNAIndex = coefNAIndex+1
            assert abs(coef_m_NA_dict[coefNAIndex][1]-coef_m[index][1])<1e-6, \
                "Expected: {0}, Actual: {1}".format(coef_m_NA_dict[coefNAIndex][1], coef_m[index][1])
            coefNAIndex=coefNAIndex+1
            
    else:
        pyunit_utils.equal_2D_tables(coef_m_NA.cell_values, coef_m.cell_values)

    
if __name__ == "__main__":
#  h2o.init(ip="192.168.86.29", port=54321, strict_version_check=False)
  pyunit_utils.standalone_test(interactions)
else:
#  h2o.init(ip="192.168.86.29", port=54321, strict_version_check=False)
  interactions()
