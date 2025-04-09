library(ggplot2)
library(dplyr)

# Step 1: Calculate the proportion of 'is_stylized' for each person and year
proportion_data <- all_data %>%
  group_by(sex, year) %>%
  summarise(
    total = n(),                      # Total count of rows (0s and 1s)
    nr_sf = sum(is_stylized),         # Sum of stylized (1s in is_stylized)
    nr_not_sf = abs(total - nr_sf),
    proportion = (nr_sf / total) * 100        # Proportion of stylized items
  )

# Create a folder to store the plots
output_dir <- "gender"
if (!dir.exists(output_dir)) {
  dir.create(output_dir)
}

data_dir <- paste0(output_dir, "/data")
if (!dir.exists(data_dir)) {
  dir.create(data_dir)
}

p <- ggplot()

for (sex in unique(all_data$sex)) {
  sex_data <- filter(proportion_data, sex == !!sex)
  
  # person_data$year <- as.factor(person_data$year)
  
  num_years = length(unique(person_data$year))
  
  # Create the plot for each person
  p <- p +
    geom_line(data = sex_data, aes(x = year, y = proportion, color = sex, group = sex)) +
    geom_point(data = sex_data, aes(x = year, y = proportion, size = total, color = sex, group = sex))
  
  # Save the plot as a PNG file
  write.table(sex_data, paste0(data_dir, "/", sex, ".tsv"), sep = "\t", row.names = FALSE)
}

p <- p +
  ggtitle("SF proportion, male vs female") +
  xlab("Year") +
  ylab("SF proportion (%)") +
  scale_y_continuous(limits = c(0,100)) +
  scale_x_continuous(breaks = seq(min(all_data$year)+1, max(all_data$year), by = 5)) +
  scale_size_continuous(range = c(0.5, 4)) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
  guides(size = guide_legend(title = "Nr. of tokens"),  color = guide_legend(title = "Gender"))

ggsave(filename = paste0(output_dir, "/", "male_vs_female.png"), plot = p, width = 14, height = 4)
