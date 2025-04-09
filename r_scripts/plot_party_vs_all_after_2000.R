library(ggplot2)
library(dplyr)

filered_data <- all_data %>%
  filter(year >= 2000)

# Step 1: Calculate the proportion of 'is_stylized' for each person and year
proportion_data <- filtered_data %>%
  group_by(party_name, year) %>%
  summarise(
    total = n(),                      # Total count of rows (0s and 1s)
    nr_sf = sum(is_stylized),         # Sum of stylized (1s in is_stylized)
    nr_not_sf = abs(total - nr_sf),
    proportion = (nr_sf / total) * 100   
  )


overall_proportion <- all_data %>%
  group_by(year) %>%
  summarise(
    total = sum(is_stylized),         # Sum of stylized (1s in is_stylized)
    count = n(),                      # Total count of rows (0s and 1s)
    proportion = (total / count) * 100        # Proportion of stylized items
  )

# Step 2: Iterate over each unique person and save their plot
unique_parties <- unique(proportion_data$party_name)

# Create a folder to store the plots
output_dir <- "party_vs_all_after_2000"
if (!dir.exists(output_dir)) {
  dir.create(output_dir)
}

data_dir <- paste0(output_dir, "/data")
if (!dir.exists(data_dir)) {
  dir.create(data_dir)
}

for (party in unique_parties) {
  party_data <- filter(proportion_data, party_name == !!party)
  
  party_data$year <- as.factor(party_data$year)
  
  overall_filtered <- filter(overall_proportion, year %in% party_data$year)
  
  overall_filtered$year <- as.factor(overall_filtered$year)
  
  num_years = length(unique(party_data$year))
  
  # Create the plot for each person
  p <- ggplot() +
    geom_line(data = overall_filtered, aes(x = year, y = proportion, group = 1, color = "All Parties"), linewidth = 1) +
    geom_line(data = party_data, aes(x = year, y = proportion, group = 1), color = 'black') +
    geom_point(data = party_data, aes(x = year, y = proportion, size = total), color = 'black') +
    ggtitle(paste("SF proportion for", party)) +
    xlab("Year") +
    ylab("SF proportion (%)") +
    scale_y_continuous(limits = c(0, 100)) +
    scale_x_discrete(drop = FALSE) +
    scale_color_manual(values = c("All Parties" = "#979797"), name = "Legend") +
    theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
    guides(size = guide_legend(title = "Nr. of tokens"), color=guide_legend(title = ""))
  
  plot_width <- max(6, num_years * 0.3)
  
  # Save the plot as a PNG file
  ggsave(filename = paste0(output_dir, "/", party, ".png"), plot = p, width = plot_width, height = 4, limitsize = FALSE)
  write.table(party_data, paste0(data_dir, "/", party, ".tsv"), sep = "\t", row.names = FALSE)
}
