# kmstr

kmstr is a Python tool designed to interface with Volkswagen services using the tillsteinbach/WeConnect-python project. kmstr monitors a variety of attributes related to your vehicles, including tracking mileage, fuel refueling sessions, routes taken, vehicle locations, and more.

## Features

- **Mileage Tracking**: Record the evolution of kilometers traveled.
- **Fuel Monitoring**: Log fuel refueling sessions.
- **Route Tracking**: Monitor the routes your vehicles have taken.
- **Location History**: Keep track of where your vehicles have been.

## Inspiration and Implementation

This project draws strong inspiration from the tillsteinbach/VWsFriend project. While VWsFriend provided a comprehensive set of features, kmstr focuses on my specific use case by removing unnecessary parts. One of the main goals of Kmstr is to modularize the data import functionality from the dashboard used for data visualization.

## Modularity

Kmstr is under active development to create a clear separation between data import and data visualization components. This architecture aims to make the tool highly modular, allowing easy extension and customization to fit different needs.

## Development

Kmstr was developed to enhance the management and tracking of my vehicles' data. If you're interested in exploring the code or contributing to the project, please check out the repository on GitHub.

## Note

This is a personal project and is not affiliated with Volkswagen or tillsteinbach. The code is available under the Creative Commons Zero v1.0 Universal License.

### Acknowledgements

This project uses the tillsteinbach/WeConnect-python API, which is licensed under the MIT License.
