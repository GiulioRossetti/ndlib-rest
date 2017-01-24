# Change Log
All notable changes to this project will be documented in this file.

## [Unrealeased]
### Added
- Website
    - REST tutorial
    - Python client tutorial
    - Model description tutorial ([ndlib](https://github.com/GiulioRossetti/ndlib))

## [0.9.2]
### Added
- Networks
	- Planted l-partition
	- Clustered Barabàsi-Albert
- Exploratories
	- ToyCore: local (community) outbreak 
	- ToyPeri: global outbreak
	- ClusteredBA_top: Kertesz Threshold test (10%-high degree nodes blocked)
	- ClusteredBA_bottom: Kertesz Threshold test (10%-low degree nodes blocked)
	- CogOp: network having powerlaw degree distribution with exponent b=1.6
	
### Changed
- Experiment Persistency Model (refactoring)

## [0.9.1]
### Added
- Models
    - Kertesz Threshold
    - Cognitive Opinion Dynamics 
- Installation
    - Docker Setup

## [0.9.0]
### Added
- Networks
    - Complete Graphs
- Models
    - QVoter
- Resources
    - Upload Graph (JSON)
- Iterators
    - Incremental updates

### Changed
- File upload/download limit (50MB)
- Experiment Persistency Model
    
## [0.8.0]
### Updated
- Experiment Persistence Handling: form unique db to individual dbs

### Added
- Access Control Allow Origin header
    
    
## [0.7.0]
### Added
- Models
    - Voter
    - Majority Rule
    - Sznajd
    
    
### Updated
- Tools
   - Python REST client (support for the new models)
   
   
## [0.6.0]
### Added
- Exploratory
    - List Exploratories
    - Get Configuration
- Tools
    - Python REST client
    
    
### Changed
- Adoption of flask-shelve for experiment persistence
    - Enabling support for multi-threaded web server
    
    
## [0.5.0]
### Added
- Experiment
    - Advanced Configuration
- Networks
    - Get Network
    
    
## [0.4.0]
### Added
- Resources
    - Real Network Endpoint List
    - Network Destroy
- Networks
    - Load Real Graph
    
    
## [0.3.0]
### Added
- Networks
    - Watts-Strogatz
- Models
    - Profile
    - Profile-Threshold
    
    
## [0.2.0]
### Added
- Networks
    - Barabasi-Albert
- Models
    - SI
    - SIS
    - SIR
- Iterators
    - Complete Run
    
    
## [0.1.0]
### Added
- Experiment 
    - Create, Describe, Reset, Destroy
- Resources
    - Models Endpoint List
    - Network Generators Endpoint List
    - Models Destroy
- Networks
    - Erdos-Renyi
- Models
    - Threshold
- Iterators
    - Single Iteration
    - Iteration Bunch
