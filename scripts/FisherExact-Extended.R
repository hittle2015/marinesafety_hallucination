# 加载必要的包
# 如果尚未安装，请取消注释以下行进行安装
# install.packages("dplyr")

library(dplyr)
# 设置工作目录到 'all_statistics.csv' 所在的位置
setwd("/Users/yuyuan/Workspace/research/manuscripts/")  # 根据需要取消注释并设置您的路径

# 定义费舍尔精确检验的函数
perform_fisher_test <- function(contingency_table) {
  test_result <- fisher.test(as.matrix(contingency_table), simulate.p.value=TRUE)
  return(test_result$p.value)
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

#compute cohen-d
cohen_d <-function(df1, df2){
  n1 <- length(df1); n2 <- length(df2)
  mean_x <- mean(df1, na.rm = TRUE); mean_y <- mean(df2, na.rm = TRUE)
  sd_pooled <- sqrt(((n1 - 1)*var(df1) + (n2 - 1)*var(df2)) / (n1 + n2 - 2))
  cohen_d <- (mean_x - mean_y) / sd_pooled
  
  return (cohen_d)
}

# 主函数
main <- function() {
  # 读取 CSV 数据
  data <- read.csv("all_statistics.csv", stringsAsFactors = FALSE)
  
  # 定义幻觉类型
  halluc_types <- c('UCE', 'OGE', 'UGE', 'MGE', 'NNE', 'DTE')
  
  # 获取唯一的学习模式和模型
  modes <- unique(data$mode)
  models <- unique(data$model)
  
  # 初始化结果数据框
  model_comparisons <- data.frame(
    Learning_Mode = character(),
    Model_1 = character(),
    Model_2 = character(),
    P_Value = numeric(),
    Cohen_d = numeric(),
    Interpretation = character(),
    stringsAsFactors = FALSE
  )
  
  mode_comparisons <- data.frame(
    Model = character(),
    Mode_1 = character(),
    Mode_2 = character(),
    P_Value = numeric(),
    Cohen_d = numeric(),
    Interpretation = character(),
    stringsAsFactors = FALSE
  )
  
  overall_model_comparisons <- data.frame(
    Model = character(),
    Mode_1 = character(),
    Mode_2 = character(),
    P_Value = numeric(),
    Cohen_d = numeric(),
    Interpretation = character(),
    stringsAsFactors = FALSE
  )
  
  
  cross_model_mode_comparisons <- data.frame(
    Model_1 = character(),
    Mode_1 = character(),
    Model_2 = character(),
    Mode_2 = character(),
    P_Value = numeric(),
    Cohen_d = numeric(),
    Interpretation = character(),
    stringsAsFactors = FALSE
  )
  
  # 任务 1：每种学习模式下的模型两两比较
  cat("=== 每种学习模式下的模型两两比较 ===\n\n")
  
  for (mode in modes) {
    cat(sprintf("学习模式：%s\n", mode))
    
    # 筛选当前学习模式的数据
    mode_data <- filter(data, mode == !!mode)
    
    # 获取模型组合
    model_pairs <- combn(models, 2, simplify = FALSE)
    
    for (pair in model_pairs) {
      model1 <- pair[1]
      model2 <- pair[2]
      
      # 获取两个模型的幻觉类型总和
      data1 <- mode_data %>%
        filter(model == model1) %>%
        select(all_of(halluc_types)) %>%
        summarise_all(sum)
      
      data2 <- mode_data %>%
        filter(model == model2) %>%
        select(all_of(halluc_types)) %>%
        summarise_all(sum)
      
      # 构建列联表
      contingency_table <- rbind(data1, data2)
      rownames(contingency_table) <- c(model1, model2)
      
      # 执行费舍尔精确检验
      p_value <- perform_fisher_test(contingency_table)
      cohen_d <- cohen_d(data1, data2)
      # 解释 p 值
      interpretation <- interpret_p_value(p_value)
      
      # 输出结果到控制台
      cat(sprintf("  比较：%s vs %s\n", model1, model2))
      cat(sprintf("    P-值: %.4f\n", p_value))
      cat(sprintf("    解释：%s\n", interpretation))
      
      # 将结果添加到模型比较结果数据框
      model_comparisons <- rbind(model_comparisons, data.frame(
        Learning_Mode = mode,
        Model_1 = model1,
        Model_2 = model2,
        P_Value = p_value,
        Cohen_d = cohen_d,
        Interpretation = interpretation,
        stringsAsFactors = FALSE
      ))
    }
    cat("\n")
  }
  # 显示所有成对检验结果
  print("相同模式不同模型成对 Fisher 精确检验结果：")
  print(model_comparisons)
  
  # 任务 2：每个模型下的学习模式两两比较
  cat("=== 单个模型下的学习模式两两比较 ===\n\n")
  
  for (model in models) {
    cat(sprintf("模型：%s\n", model))
    
    # 筛选当前模型的数据
    model_data <- filter(data, model == !!model)
    
    # 获取学习模式组合
    mode_pairs <- combn(modes, 2, simplify = FALSE)
    
    for (pair in mode_pairs) {
      mode1 <- pair[1]
      mode2 <- pair[2]
      
      # 获取两个学习模式的幻觉类型总和
      data1 <- model_data %>%
        filter(mode == mode1) %>%
        select(all_of(halluc_types)) %>%
        summarise_all(sum)
      
      data2 <- model_data %>%
        filter(mode == mode2) %>%
        select(all_of(halluc_types)) %>%
        summarise_all(sum)
      
      # 构建列联表
      contingency_table <- rbind(data1, data2)
      rownames(contingency_table) <- c(mode1, mode2)
      
      # 执行费舍尔精确检验
      p_value <- perform_fisher_test(contingency_table)
      cohen_d <- cohen_d(data1, data2)
      # 解释 p 值
      interpretation <- interpret_p_value(p_value)
      
      # 输出结果到控制台
      cat(sprintf("  比较：%s vs %s\n", mode1, mode2))
      cat(sprintf("    P-值: %.4f\n", p_value))
      cat(sprintf("    解释：%s\n", interpretation))
      
      # 将结果添加到模式比较结果数据框
      mode_comparisons <- rbind(mode_comparisons, data.frame(
        Model = model,
        Mode_1 = mode1,
        Mode_2 = mode2,
        P_Value = p_value,
        Cohen_d = cohen_d,
        Interpretation = interpretation,
        stringsAsFactors = FALSE
      ))
    }
    cat("\n")
  }
  # 显示所有成对检验结果
  print("相同模型不同模式成对 Fisher 精确检验结果：")
  print(mode_comparisons)
  
  # 任务 3：不同模型在所有学习模式下的整体表现比较
  cat("=== 不同模型在所有学习模式下的整体表现比较 ===\n\n")
  
  model_overall_pairs <- combn(models, 2, simplify = FALSE)
  
  for (pair in model_overall_pairs) {
    model1 <- pair[1]
    model2 <- pair[2]
    
    # 获取两个模型在所有学习模式下的幻觉类型总和
    data1 <- data %>%
      filter(model == model1) %>%
      select(all_of(halluc_types)) %>%
      summarise_all(sum)
    
    data2 <- data %>%
      filter(model == model2) %>%
      select(all_of(halluc_types)) %>%
      summarise_all(sum)
    
    # 构建列联表
    contingency_table <- rbind(data1, data2)
    rownames(contingency_table) <- c(model1, model2)
    
    # 执行费舍尔精确检验
    p_value <- perform_fisher_test(contingency_table)
    cohen_d <- cohen_d(data1, data2)
    # 解释 p 值
    interpretation <- interpret_p_value(p_value)
    
    # 输出结果到控制台
    cat(sprintf("  比较：%s vs %s (所有学习模式)\n", model1, model2))
    cat(sprintf("    P-值: %.4f\n", p_value))
    cat(sprintf("    解释：%s\n", interpretation))
    
    # 将结果添加到整体模型比较结果数据框
    overall_model_comparisons <- rbind(overall_model_comparisons, data.frame(
      Comparison = paste(model1, "vs", model2, "(所有学习模式)"),
      P_Value = p_value,
      Cohen_d = cohen_d,
      Interpretation = interpretation,
      stringsAsFactors = FALSE
    ))
  }
  # 显示所有成对检验结果
  print("不同模型在所有学习模式下的整体 Fisher 精确检验结果：")
  print(overall_model_comparisons)
  
  cat("\n")
  
  # 任务 4：不同模型在不同学习模式下的两两比较
  cat("=== 不同模型在不同学习模式下的两两比较 ===\n\n")
  
  # 创建所有模型-模式组合
  model_mode_combinations <- expand.grid(Model = models, Mode = modes, stringsAsFactors = FALSE)
  
  # 获取所有唯一的两两组合（无序）
  cross_pairs <- combn(nrow(model_mode_combinations), 2, simplify = FALSE)
  
  for (pair in cross_pairs) {
    row1 <- model_mode_combinations[pair[1], ]
    row2 <- model_mode_combinations[pair[2], ]
    
    model1 <- row1$Model
    mode1 <- row1$Mode
    model2 <- row2$Model
    mode2 <- row2$Mode
    
    # 跳过相同模型和相同模式的比较 (避免重复或自比较)
    if (model1 == model2 && mode1 == mode2) {
      next
    }
    
    # 获取第一个模型-模式组合的幻觉类型总和
    data1 <- data %>%
      filter(model == model1, mode == mode1) %>%
      select(all_of(halluc_types)) %>%
      summarise_all(sum)
    
    # 获取第二个模型-模式组合的幻觉类型总和
    data2 <- data %>%
      filter(model == model2, mode == mode2) %>%
      select(all_of(halluc_types)) %>%
      summarise_all(sum)
    
    # 检查是否有数据可进行比较
    if (all(data1 == 0) || all(data2 == 0)) {
      p_value <- NA
      interpretation <- "无法解释 (至少一个组合的数据为零)"
    } else {
      # 构建列联表
      contingency_table <- rbind(data1, data2)
      rownames(contingency_table) <- c(paste(model1, mode1, sep = "_"), paste(model2, mode2, sep = "_"))
      
      # 执行费舍尔精确检验
      p_value <- perform_fisher_test(contingency_table)
      cohen_d <- cohen_d(data1, data2)
      # 解释 p 值
      interpretation <- interpret_p_value(p_value)
    }
    
    # 输出结果到控制台
    cat(sprintf("  比较：%s 在 %s 模式 vs %s 在 %s 模式\n", model1, mode1, model2, mode2))
    cat(sprintf("    P-值: %s\n", ifelse(is.na(p_value), "NA", sprintf("%.4f", p_value))))
    cat(sprintf("    解释：%s\n", interpretation))
    
    # 将结果添加到跨模型-模式比较结果数据框
    cross_model_mode_comparisons <- rbind(cross_model_mode_comparisons, data.frame(
      Model_1 = model1,
      Mode_1 = mode1,
      Model_2 = model2,
      Mode_2 = mode2,
      P_Value = p_value,
      Cohen_d = cohen_d,
      Interpretation = interpretation,
      stringsAsFactors = FALSE
    ))
  }
  # 显示所有成对检验结果
  print("不同模型在不同学习模式下的 Fisher 精确检验结果：")
  print(cross_model_mode_comparisons)
  cat("\n")
  # 将比较结果写入 CSV 文件
  write.csv(model_comparisons, "pairwise_model_comparisons.csv", row.names = FALSE)
  write.csv(mode_comparisons, "pairwise_mode_comparisons.csv", row.names = FALSE)
  write.csv(overall_model_comparisons, "overall_model_comparisons.csv", row.names = FALSE)
  write.csv(cross_model_mode_comparisons, "cross_model_mode_comparisons.csv", row.names = FALSE)
  
  cat("比较结果已保存到 'pairwise_model_comparisons.csv', 'pairwise_mode_comparisons.csv', 'overall_model_comparisons.csv' 和 'cross_model_mode_comparisons.csv'。\n")
}

# 执行主函数
main()