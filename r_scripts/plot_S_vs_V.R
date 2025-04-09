library(ggplot2)
library(dplyr)

output_dir <- "s_vs_v"
if (!dir.exists(output_dir)) {
  dir.create(output_dir)
}

# data_dir <- paste0(output_dir, "/data")
# if (!dir.exists(data_dir)) {
#   dir.create(data_dir)
# }

selected_parties <- c("party.S", "party.V")
filtered_data <- all_data %>%
  filter(party_id %in% selected_parties & year >= 2000)

other_filtered <- all_data %>%
  filter(! party_id %in% selected_parties & year >= 2000)

proportion_data <- filtered_data %>%
  group_by(party_id, party_name, year) %>%
  summarise(
    total = n(),                      # Total count of rows (0s and 1s)
    nr_sf = sum(is_stylized),         # Sum of stylized (1s in is_stylized)
    nr_not_sf = abs(total - nr_sf),
    proportion = (nr_sf / total) * 100        # Proportion of stylized items
  )

other_proportion <- other_filtered %>%
  group_by(year) %>%
  summarise(
    total = n(),                      # Total count of rows (0s and 1s)
    nr_sf = sum(is_stylized),         # Sum of stylized (1s in is_stylized)
    nr_not_sf = abs(total - nr_sf),
    proportion = (nr_sf / total) * 100        # Proportion of stylized items
  )

other_proportion$year <- as.factor(other_proportion$year)

p <- ggplot() +
  geom_line(data = other_proportion, aes(x = year, y = proportion, color = "Other parties", group = "other"), linewidth = 1)
  

for (party_id in selected_parties) {
  
  party_data <- filter(proportion_data, party_id == !!party_id)
  party_data$year <- as.factor(party_data$year)
  
  p <- p +
    geom_line(data = party_data, aes(x = year, y = proportion, color = as.factor(party_name), group = party_id), linewidth = 1) +
    geom_point(data = party_data, aes(x = year, y = proportion, size = total, color = as.factor(party_name)))
  
  write.table(party_data, file = paste0(output_dir, "/", party_id, ".tsv"), sep="\t", row.names = FALSE)
}

party_colors <- c("Samfylking" = "#B51015",
                  "Sjálfstæðisflokkur" = "#0E89B8",
                  "Framsóknarflokkur" = "#2F6B10",
                  "Vinstrihreyfingin - grænt framboð" = "#6A9A43",
                  "Viðreisn" = "#DC8F54",
                  "Other parties" = "#979797")

p <- p +
  ggtitle("SF Proportion for S and V parties (2000 and Up)") +
  xlab("Year") +
  ylab("SF proportion (%)") +
  scale_y_continuous(limits = c(0, 100)) +  # Set the y-axis to range from 0 to 100 percent
  scale_color_manual(values = party_colors, name = "Parties") +    # Color the lines based on the party names
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
  guides(size = guide_legend(title = "Nr. of tokens"))

ggsave(filename = paste0(output_dir, "/", "s_vs_v.png"), plot = p, width = 10, height = 6, limitsize = FALSE)
