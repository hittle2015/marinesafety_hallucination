# Load necessary libraries
library(dplyr)
library(tidyr)  #
# 设置工作目录到 data 所在的位置
setwd("/Users/yuyuan/Workspace/research/manuscripts/")  # 根据需要取消注释并设置您的路径
# Read the CSV file
data <- read.csv("grouped_evaluation_metrics.csv")

str(data)
# Convert data to long format for easier manipulation
data_long <- data %>%
  pivot_longer(cols = c(BLEU, ROUGE.W, METEOR, BERT_P, BERT_R, BERT_F1), 
               names_to = "Metric", 
               values_to = "Score")

#compute cohen-d
cohen_d <-function(df1, df2){
  n1 <- length(df1); n2 <- length(df2)
  mean_x <- mean(df1, na.rm = TRUE); mean_y <- mean(df2, na.rm = TRUE)
  sd_pooled <- sqrt(((n1 - 1)*var(df1) + (n2 - 1)*var(df2)) / (n1 + n2 - 2))
  cohen_d <- (mean_x - mean_y) / sd_pooled
  
  return (cohen_d)
}

# 定义解释 p 值的函数
interpret_p_value <- function(p) {
  if (is.na(p)) {
    return("无法解释 (p 值缺失)")
  } else if (p < 0.001) {
    return("极显著差异 (p < 0.001)")
  } else if (p < 0.01) {
    return("高度显著差异 (p < 0.01)")
  } else if (p < 0.05) {
    return("显著差异 (p < 0.05)")
  } else {
    return("无显著差异 (p >= 0.05)")
  }
}


#1 Function to perform paired t-tests for a given learning mode
paired_comparison_models <- function(df) {
  models <- unique(df$Model)
  results <- data.frame()
  
  
  # Perform paired t-tests for each pair of models
  for (i in 1:(length(models) - 1)) {
    for (j in (i + 1):length(models)) {
      model1 <- models[i]
      model2 <- models[j]
      
      # Filter data for the two models
      scores1 <- df %>% filter(Model == model1) %>% pull(Score)
      scores2 <- df %>% filter(Model == model2) %>% pull(Score)
      
      # Perform paired t-test
      t_test_result <- t.test(scores1, scores2, paired = TRUE)
      p_value = t_test_result$p.value
      t_statistic = t_test_result$statistic
      cohen_d = cohen_d (scores1, scores2)
      # Store results
      results <- rbind(results, data.frame(
        Learning_Mode = unique(df$Learning_Mode),
        Model1 = model1,
        Model2 = model2,
        t_statistic = t_statistic,
        p_value = p_value,
        cohen_d <- cohen_d,
        Interpretation = interpret_p_value(p_value),
        stringsAsFactors = FALSE
      ))
    }
  }
  
  return(results)
}


#2 Function to compare model differences across all learning modes
compare_learning_modes <- function(df) {
  models <- unique(df$Model)
  modes <- unique(df$Learning_Mode)
  results <- data.frame()
  
  # Perform paired t-tests for each pair of modes across all learning models
  for (i in 1:(length(modes) - 1)) {
    for (j in (i + 1):length(modes)) {
      mode1 <- modes[i]
      mode2 <- modes[j]
      
      # Gather scores for both models across all learning modes
      scores1 <- df %>% filter(Learning_Mode == mode1) %>% pull(Score)
      scores2 <- df %>% filter(Learning_Mode == mode2) %>% pull(Score)
      
      # Perform paired t-test
      t_test_result <- t.test(scores1, scores2, paired = TRUE)
      p_value = t_test_result$p.value
      t_statistic = t_test_result$statistic
      cohen_d = cohen_d (scores1, scores2)
      # Store results
      results <- rbind(results, data.frame(
        Model = models,
        Mode1 = mode1,
        Mode2 = mode2,
        t_statistic = t_statistic,
        p_value = p_value,
        cohen_d = cohen_d,
        Interpretation = interpret_p_value(p_value),
        stringsAsFactors = FALSE
      ))
    }
  }
  
  return(results)
}

  
#3 Function to compare model differences across all learning modes
compare_models_over_all_modes <- function(df) {
    models <- unique(df$Model)
    results <- data.frame()
    
    # Perform paired t-tests for each pair of models across all learning modes
    for (i in 1:(length(models) - 1)) {
      for (j in (i + 1):length(models)) {
        model1 <- models[i]
        model2 <- models[j]
        
        # Gather scores for both models across all learning modes
        scores1 <- df %>% filter(Model == model1) %>% pull(Score)
        scores2 <- df %>% filter(Model == model2) %>% pull(Score)
        
        # Perform paired t-test
        t_test_result <- t.test(scores1, scores2, paired = TRUE)
        
        p_value = t_test_result$p.value
        t_statistic = t_test_result$statistic
        cohen_d = cohen_d (scores1, scores2)
        # Store results
        results <- rbind(results, data.frame(
          Model1 = model1,
          Model2 = model2,
          # Learning_Mode1 = mode1,
          # Learning_Mode2 = mode2,
          t_statistic = t_statistic,
          p_value = p_value,
          cohen_d = cohen_d,
          Interpretation = interpret_p_value(p_value)
        ))
      }
    }
    
    return(results)
 }
  
# Function for cross-model and cross-learning mode t-tests
cross_model_cross_learning_mode_tests <- function(df) {
  models <- unique(df$Model)
  modes <- unique(df$Learning_Mode)
  results <- data.frame()
  
  # Create all model-mode combinations
  model_mode_combinations <- expand.grid(Model = models, Mode = modes, stringsAsFactors = FALSE)
  
  # Get all unique pairs (unordered)
  cross_pairs <- combn(nrow(model_mode_combinations), 2, simplify = FALSE)
  
  for (pair in cross_pairs) {
    row1 <- model_mode_combinations[pair[1], ]
    row2 <- model_mode_combinations[pair[2], ]
    
    model1 <- row1$Model
    mode1 <- row1$Mode
    model2 <- row2$Model
    mode2 <- row2$Mode
    
    # Skip identical model-mode comparisons
    if (model1 == model2 && mode1 == mode2) {
      next
    }
    
    # Gather scores for both model-mode combinations
    scores1 <- df %>% filter(Model == model1, Learning_Mode == mode1) %>% pull(Score)
    scores2 <- df %>% filter(Model == model2, Learning_Mode == mode2) %>% pull(Score)
    cohen_d = cohen_d (scores1, scores2)
    if (length(scores1) > 0 && length(scores2) > 0) {
      t_test_result <- t.test(scores1, scores2, paired = TRUE)
      results <- rbind(results, data.frame(
        Model_1 = model1,
        Mode_1 = mode1,
        Model_2 = model2,
        Mode_2 = mode2,
        P_Value = t_test_result$p.value,
        t_statistic = t_test_result$statistic,
        cohen_d = cohen_d,
       
        Interpretation = interpret_p_value(t_test_result$p.value),
        stringsAsFactors = FALSE
      ))
    }
  }
  
  # Display all pairwise test results
  print("不同模型在不同学习模式下的 t 检验结果：")
  print(results)
}
# 1Perform paired t-tests for each learning mode for models
t_test_results_models <- data_long %>%
  group_by(Learning_Mode) %>%
  do(paired_comparison_models(.))

# Save results for model comparisons to CSV
write.csv(t_test_results_models, "t_test_results_models.csv", row.names = FALSE)

# 2Print results for model comparisons
print(t_test_results_models)

# Perform paired t-tests for each model across learning modes
t_test_results_learning_modes <- data_long %>%                                
  group_by(Model) %>%
  do(compare_learning_modes(.))

# Save results for learning mode comparisons to CSV
write.csv(t_test_results_learning_modes, "t_test_results_learning_modes.csv", row.names = FALSE)

# Print results for learning mode comparisons
print(t_test_results_learning_modes)

# Perform paired t-tests for model differences over all learning modes
t_test_results_all_models <- compare_models_over_all_modes(data_long)

# Save results for model differences to CSV
write.csv(t_test_results_all_models, "t_test_results_all_models.csv", row.names = FALSE)

# Print results for model differences over all learning modes
print(t_test_results_all_models)

# Perform cross-model and cross-learning mode t-tests
t_test_results_cross_model_learning_mode <- cross_model_cross_learning_mode_tests(data_long)

# Save results for cross-model and cross-learning mode comparisons to CSV
write.csv(t_test_results_cross_model_learning_mode, "t_test_results_cross_model_learning_mode.csv", row.names = FALSE)

# Print results for cross-model and cross-learning mode comparisons
print(t_test_results_cross_model_learning_mode)