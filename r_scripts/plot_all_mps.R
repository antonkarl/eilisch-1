library(ggplot2)
library(dplyr)

# Step 1: Calculate the proportion of 'is_stylized' for each person and year
proportion_data <- all_data %>%
  group_by(person, year) %>%
  summarise(
    total = n(),                      # Total count of rows (0s and 1s)
    nr_sf = sum(is_stylized),         # Sum of stylized (1s in is_stylized)
    nr_not_sf = abs(total - nr_sf),
    proportion = (nr_sf / total) * 100        # Proportion of stylized items
  )

# Step 2: Iterate over each unique person and save their plot
unique_persons <- unique(proportion_data$person)

# Create a folder to store the plots
output_dir <- "all_mps"
if (!dir.exists(output_dir)) {
  dir.create(output_dir)
}

data_dir <- paste0(output_dir, "/data")
if (!dir.exists(data_dir)) {
  dir.create(data_dir)
}

for (person in unique_persons) {
  person_data <- filter(proportion_data, person == !!person)
  
  person_data$year <- as.factor(person_data$year)
  
  num_years = length(unique(person_data$year))
  
  # Create the plot for each person
  p <- ggplot(person_data, aes(x = year, y = proportion)) +
    geom_line(group = 1) +
    geom_point(aes(size = total)) +
    ggtitle(paste("SF proportion for", person)) +
    xlab("Year") +
    ylab("SF proportion (%)") +
    ylim(0, 100) +
    scale_x_discrete(drop = FALSE) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
    guides(size = guide_legend(title = "Nr. of tokens"), color = guide_legend(title = "Gender"))
  
  plot_width <- max(6, num_years * 0.5)
  
  # Save the plot as a PNG file
  ggsave(filename = paste0(output_dir, "/", person, ".png"), plot = p, width = plot_width, height = 4)
  write.table(person_data, paste0(data_dir, "/", person, ".tsv"), sep = "\t", row.names = FALSE)
}
